from kivymd.app import MDApp
from kivy.lang import Builder
# Importamos a classe de Interface do outro ficheiro
from clientemodbus import ModbusUI

class ModbusApp(MDApp):
    def build(self):
        # Carrega o layout visual
        Builder.load_file("base.kv")
        
        # Retorna a classe ModbusUI que importámos do clientemodbus.py
        return ModbusUI()

if __name__ == '__main__':
    ModbusApp().run()