import struct
from pymodbus.client import ModbusTcpClient
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock

class ClienteMODBUS:
    """
    Classe exclusiva para a comunicação Modbus TCP.
    """
    def __init__(self, server_ip="127.0.0.1", porta=502):
        self._host = server_ip
        self._porta = int(porta)
        self._cliente = ModbusTcpClient(host=self._host, port=self._porta)
        self._conectado = False

    def conectar(self, server_ip, porta):
        self._cliente.host = server_ip
        self._cliente.port = int(porta)
        self._conectado = self._cliente.connect()
        return self._conectado

    def desconectar(self):
        self._cliente.close()
        self._conectado = False

    def esta_conectado(self):
        return self._conectado

    # Funções de Leitura
    def ler_holding_register(self, addr):
        resp = self._cliente.read_holding_registers(address=addr, count=1, device_id=1)
        return resp.registers if resp and not resp.isError() else None

    def ler_coil(self, addr):
        resp = self._cliente.read_coils(address=addr, count=1, device_id=1)
        return resp.bits[0] if resp and not resp.isError() else None

    def ler_input_register(self, addr):
        resp = self._cliente.read_input_registers(address=addr, count=1, device_id=1)
        return resp.registers if resp and not resp.isError() else None

    def ler_discrete_input(self, addr):
        resp = self._cliente.read_discrete_inputs(address=addr, count=1, device_id=1)
        return resp.bits[0] if resp and not resp.isError() else None

    def ler_float32(self, addr):
        regs = self.ler_holding_register(addr) # Aqui necessita ler 2 registos se for float32 real (count=2)
        resp = self._cliente.read_holding_registers(address=addr, count=2, device_id=1)
        if resp and not resp.isError() and len(resp.registers) == 2:
            b = struct.pack('>HH', resp.registers[0], resp.registers[1])
            return struct.unpack('>f', b)[0]
        return None

    def ler_bits_registrador(self, addr):
        regs = self.ler_holding_register(addr)
        if regs:
            return [(regs[0] >> i) & 1 for i in range(16)]
        return None

    # Funções de Escrita
    def escrever_holding_register(self, addr, valor):
        resp = self._cliente.write_register(address=addr, value=int(valor), device_id=1)
        return bool(resp and not resp.isError())

    def escrever_coil(self, addr, valor):
        resp = self._cliente.write_coil(address=addr, value=bool(int(valor)), device_id=1)
        return bool(resp and not resp.isError())

    def escrever_float32(self, addr, valor):
        b = struct.pack('>f', float(valor))
        regs = [struct.unpack('>H', b[0:2])[0], struct.unpack('>H', b[2:4])[0]]
        resp = self._cliente.write_registers(address=addr, values=regs, device_id=1)
        return bool(resp and not resp.isError())

    def escrever_bit_individual(self, addr, bit_index, valor_bit):
        regs = self.ler_holding_register(addr)
        if not regs: return False
        novo_valor = (regs[0] | (1 << bit_index)) if valor_bit == 1 else (regs[0] & ~(1 << bit_index))
        return self.escrever_holding_register(addr, novo_valor)


class ModbusUI(MDScreen):
    """
    Classe de interface que o utilizador forneceu.
    Liga a interface visual KivyMD com a classe ClienteMODBUS.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Instancia a comunicação Modbus e liga-a à interface
        self.cliente = ClienteMODBUS()
        self.evento_recorrente = None
        self.tipo_selecionado = "Holding Register"
        self.menu_tipos = None

    def abrir_menu_tipos(self):
        tipos = ["Holding Register", "Coil", "Input Register", "Discrete Input", "Float32", "Bit de Registrador"]
        menu_items = [
            {
                "text": tipo,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=tipo: self.selecionar_tipo(x),
            } for tipo in tipos
        ]
        self.menu_tipos = MDDropdownMenu(
            caller=self.ids.btn_tipo,
            items=menu_items,
            width_mult=4,
        )
        self.menu_tipos.open()

    def selecionar_tipo(self, tipo):
        self.tipo_selecionado = tipo
        self.ids.btn_tipo.text = tipo
        self.menu_tipos.dismiss()

    def conectar(self):
        ip = self.ids.txt_ip.text
        porta = self.ids.txt_porta.text
        try:
            if self.cliente.conectar(ip, porta):
                self.atualizar_status(f"Conectado com sucesso a {ip}:{porta}")
            else:
                self.atualizar_status(f"Falha ao conectar em {ip}:{porta}")
        except Exception as e:
            self.atualizar_status(f"Erro na conexão: {str(e)}")

    def desconectar(self):
        if self.evento_recorrente:
            self.ids.chk_recorrente.active = False
        self.cliente.desconectar()
        self.atualizar_status("Desconectado do servidor.")

    def executar_leitura(self):
        if not self.cliente.esta_conectado():
            self.atualizar_status("Erro: Cliente Modbus não está conectado.")
            return

        try:
            addr = int(self.ids.txt_endereco.text)
            resultado = None

            if self.tipo_selecionado == "Holding Register":
                resultado = self.cliente.ler_holding_register(addr)
                if isinstance(resultado, list): resultado = resultado[0]
            elif self.tipo_selecionado == "Coil":
                resultado = self.cliente.ler_coil(addr)
            elif self.tipo_selecionado == "Input Register":
                resultado = self.cliente.ler_input_register(addr)
                if isinstance(resultado, list): resultado = resultado[0]
            elif self.tipo_selecionado == "Discrete Input":
                resultado = self.cliente.ler_discrete_input(addr)
            elif self.tipo_selecionado == "Float32":
                val = self.cliente.ler_float32(addr)
                resultado = f"{val:.4f}" if val is not None else None
            elif self.tipo_selecionado == "Bit de Registrador":
                bits = self.cliente.ler_bits_registrador(addr)
                if bits:
                    resultado = f"Bits [0-15]: {bits}"

            if resultado is not None:
                self.atualizar_status(f"[Leitura] Endereço {addr} ({self.tipo_selecionado}): {resultado}")
            else:
                self.atualizar_status(f"[Leitura] Falha ao ler endereço {addr}.")

        except ValueError:
            self.atualizar_status("Erro: O endereço deve ser um número inteiro válido.")
        except Exception as e:
            self.atualizar_status(f"Erro na leitura: {str(e)}")

    def executar_escrita(self):
        if not self.cliente.esta_conectado():
            self.atualizar_status("Erro: Cliente Modbus não está conectado.")
            return

        try:
            addr = int(self.ids.txt_endereco.text)
            valor_text = self.ids.txt_valor.text
            ok = False

            if self.tipo_selecionado == "Holding Register":
                ok = self.cliente.escrever_holding_register(addr, int(valor_text))
            elif self.tipo_selecionado == "Coil":
                ok = self.cliente.escrever_coil(addr, int(valor_text))
            elif self.tipo_selecionado == "Float32":
                ok = self.cliente.escrever_float32(addr, float(valor_text))
            elif self.tipo_selecionado == "Bit de Registrador":
                bit_idx = int(self.ids.txt_bit_index.text)
                ok = self.cliente.escrever_bit_individual(addr, bit_idx, int(valor_text))
            else:
                self.atualizar_status(f"Escrita não suportada para o tipo {self.tipo_selecionado}.")
                return

            if ok:
                self.atualizar_status(f"[Escrita] Sucesso no endereço {addr}.")
            else:
                self.atualizar_status(f"[Escrita] Falha ao escrever no endereço {addr}.")

        except ValueError:
            self.atualizar_status("Erro: Verifique se o endereço, valor e índice são numéricos válidos.")
        except Exception as e:
            self.atualizar_status(f"Erro na escrita: {str(e)}")

    def alternar_leitura_recorrente(self, checkbox, active):
        if active:
            if not self.cliente.esta_conectado():
                self.atualizar_status("Conecte ao servidor antes de iniciar a leitura recorrente.")
                checkbox.active = False
                return
            self.evento_recorrente = Clock.schedule_interval(lambda dt: self.executar_leitura(), 1.0)
            self.atualizar_status("Leitura recorrente ativada (1s).")
        else:
            if self.evento_recorrente:
                Clock.unschedule(self.evento_recorrente)
                self.evento_recorrente = None
            self.atualizar_status("Leitura recorrente desativada.")

    def atualizar_status(self, mensagem):
        self.ids.lbl_status.text = mensagem