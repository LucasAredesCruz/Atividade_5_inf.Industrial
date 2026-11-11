from pyModbusTCP.server import DataBank, ModbusServer
import struct
import random
from time import sleep

class ServidorMODBUS:
    def __init__(self, host_ip="127.0.0.1", port=502):
        self._db = DataBank()
        self._server = ModbusServer(host=host_ip, port=port, no_block=True, data_bank=self._db)
        self.setpoint = 25.5
        self.vazao = 10.0
        
        # Inicializa Coils
        self._db.set_coils(0, [True, False, True, True])
        
        # Inicializa Holding Registers e Floats de Teste
        self._db.set_holding_registers(0, [100])
        self._db.set_holding_registers(10, self.float_to_regs(self.setpoint))
        self._db.set_holding_registers(12, self.float_to_regs(self.vazao))
        self._db.set_holding_registers(20, [0b0000000001000001]) # Bit 0 e Bit 6 ativos

    def float_to_regs(self, f_val):
        b = struct.pack('>f', float(f_val))
        return [struct.unpack('>H', b[0:2])[0], struct.unpack('>H', b[2:4])[0]]
    
    def regs_to_float(self, regs):
        b = struct.pack('>HH', regs[0], regs[1])
        return struct.unpack('>f', b)[0]

    def run(self):
        self._server.start()
        print("Servidor MODBUS TCP iniciado em 127.0.0.1:502. Pressione Ctrl+C para encerrar.")
        try:
            while True:
                # Simula variação de vazão e temperatura
                self.vazao += random.uniform(-0.5, 0.5)
                self._db.set_holding_registers(12, self.float_to_regs(self.vazao))
                sleep(1)
        except KeyboardInterrupt:
            print("\nServidor encerado.")
            self._server.stop()

if __name__ == '__main__':
    servidor = ServidorMODBUS('127.0.0.1', 502)
    servidor.run()