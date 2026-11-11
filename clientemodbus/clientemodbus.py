from pymodbus.client import ModbusTcpClient
import struct

class ClienteMODBUS:
    """
    Classe de comunicação Modbus TCP isolada da interface gráfica.
    """
    def __init__(self, server_ip="127.0.0.1", porta=502):
        self._host = server_ip
        self._porta = int(porta)
        self._cliente = None
        self._conectado = False

    def conectar(self, server_ip=None, porta=None):
        if server_ip:
            self._host = server_ip
        if porta:
            self._porta = int(porta)
            
        self._cliente = ModbusTcpClient(host=self._host, port=self._porta)
        self._conectado = self._cliente.connect()
        return self._conectado

    def desconectar(self):
        if self._cliente:
            self._cliente.close()
            self._conectado = False

    def esta_conectado(self):
        return self._conectado and self._cliente and self._cliente.is_socket_open()

    # --- LEITURAS ---

    def ler_holding_register(self, addr, count=1):
        if not self.esta_conectado():
            return None
        resp = self._cliente.read_holding_registers(address=addr, count=count, slave=1)
        if resp and not resp.isError():
            return resp.registers
        return None

    def ler_input_register(self, addr, count=1):
        if not self.esta_conectado():
            return None
        resp = self._cliente.read_input_registers(address=addr, count=count, slave=1)
        if resp and not resp.isError():
            return resp.registers
        return None

    def ler_coil(self, addr):
        if not self.esta_conectado():
            return None
        resp = self._cliente.read_coils(address=addr, count=1, slave=1)
        if resp and not resp.isError():
            return resp.bits[0]
        return None

    def ler_discrete_input(self, addr):
        if not self.esta_conectado():
            return None
        resp = self._cliente.read_discrete_inputs(address=addr, count=1, slave=1)
        if resp and not resp.isError():
            return resp.bits[0]
        return None

    def ler_float32(self, addr):
        regs = self.ler_holding_register(addr, 2)
        if regs and len(regs) == 2:
            b = struct.pack('>HH', regs[0], regs[1])
            return struct.unpack('>f', b)[0]
        return None

    def ler_bits_registrador(self, addr):
        regs = self.ler_holding_register(addr, 1)
        if regs:
            valor = regs[0]
            bits = [(valor >> i) & 1 for i in range(16)]
            return bits
        return None

    # --- ESCRITAS ---

    def escrever_holding_register(self, addr, valor):
        if not self.esta_conectado():
            return False
        resp = self._cliente.write_register(address=addr, value=int(valor), slave=1)
        return bool(resp and not resp.isError())

    def escrever_coil(self, addr, valor):
        if not self.esta_conectado():
            return False
        resp = self._cliente.write_coil(address=addr, value=bool(int(valor)), slave=1)
        return bool(resp and not resp.isError())

    def escrever_float32(self, addr, valor):
        if not self.esta_conectado():
            return False
        b = struct.pack('>f', float(valor))
        regs = [struct.unpack('>H', b[0:2])[0], struct.unpack('>H', b[2:4])[0]]
        resp = self._cliente.write_registers(address=addr, values=regs, slave=1)
        return bool(resp and not resp.isError())

    def escrever_bit_individual(self, addr, bit_index, valor_bit):
        if not (0 <= bit_index <= 15) or valor_bit not in [0, 1]:
            return False
        regs = self.ler_holding_register(addr, 1)
        if not regs:
            return False
        
        valor_atual = regs[0]
        if valor_bit == 1:
            novo_valor = valor_atual | (1 << bit_index)
        else:
            novo_valor = valor_atual & ~(1 << bit_index)
            
        return self.escrever_holding_register(addr, novo_valor)