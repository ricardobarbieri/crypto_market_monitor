import tkinter as tk
from tkinter import ttk
import datetime
import pytz
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from collections import deque
from binance.client import Client
from binance.exceptions import BinanceAPIException

class CryptoMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Market Monitor")
        
        # Configuração das criptomoedas por aba
        self.tab1_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]  # Blue Chips
        self.tab2_pairs = ["UNIUSDT", "AAVEUSDT", "LINKUSDT", "DOTUSDT"]           # DeFi
        self.tab3_pairs = ["XRPUSDT", "DOGEUSDT", "MATICUSDT", "AVAXUSDT"]        # Altcoins
        
        # Inicializar cliente Binance (modo público)
        self.client = Client("", "")  # API pública não precisa de credenciais
        
        # Configuração específica para 1366x768
        self.screen_width = 1366
        self.screen_height = 768
        window_width = 1340
        window_height = 720
        
        # Centralizando a janela
        x = (self.screen_width - window_width) // 2
        y = (self.screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#2c3e50')

        # Dicionário para armazenar dados históricos
        self.crypto_data = {}
        self.bull_bear_data = {}

        # Configurações de atualização
        self.update_interval = 60  # 1 minuto
        self.data_points = 30      # 30 pontos no gráfico
        
        self.setup_styles()
        self.setup_gui()
        
        # Inicializar dados históricos
        self.initialize_crypto_data()
        
        # Iniciar threads de atualização
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure('TNotebook', 
                       background='#2c3e50',
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background='#34495e',
                       foreground='white',
                       padding=[15, 5],
                       font=('Arial', 10, 'bold'))
        
        style.map('TNotebook.Tab',
                 background=[('selected', '#2c3e50')],
                 foreground=[('selected', '#3498db')])
        
        style.configure('TProgressbar',
                       thickness=15,
                       borderwidth=0,
                       troughcolor='#34495e',
                       background='#27ae60')
                       
        style.configure("Custom.Vertical.TScrollbar",
                       background='#34495e',
                       bordercolor='#2c3e50',
                       arrowcolor='white',
                       troughcolor='#2c3e50')

    def get_binance_klines(self, symbol, interval='1m', limit=30):
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            data = []
            for k in klines:
                data.append({
                    'timestamp': datetime.datetime.fromtimestamp(k[0] / 1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            
            return data
        except BinanceAPIException as e:
            print(f"Erro ao obter dados da Binance para {symbol}: {e}")
            return []

    def setup_gui(self):
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(padx=5, pady=5, fill='both', expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg='#2c3e50')
        header_frame.pack(fill='x', pady=2)

        # Relógio e BTC Dominance
        info_frame = tk.Frame(header_frame, bg='#2c3e50')
        info_frame.pack(side='left', padx=5)

        self.clock_label = tk.Label(
            info_frame,
            font=('Arial', 16),
            bg='#2c3e50',
            fg='white'
        )
        self.clock_label.pack(side='left', padx=5)

        self.btc_dominance_label = tk.Label(
            info_frame,
            font=('Arial', 12),
            bg='#2c3e50',
            fg='white',
            text="BTC Dom: --"
        )
        self.btc_dominance_label.pack(side='left', padx=15)

        self.market_cap_label = tk.Label(
            info_frame,
            font=('Arial', 12),
            bg='#2c3e50',
            fg='white',
            text="Market Cap: --"
        )
        self.market_cap_label.pack(side='left', padx=15)

        # Container com scrollbar
        container = tk.Frame(main_frame, bg='#2c3e50')
        container.pack(fill='both', expand=True)

        # Canvas
        self.canvas = tk.Canvas(container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", 
                                command=self.canvas.yview,
                                style="Custom.Vertical.TScrollbar")

        # Notebook
        self.notebook = ttk.Notebook(self.canvas)

        # Configurar scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack elementos
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Criar as abas
        self.tab1 = self.create_crypto_tab("Blue Chips", self.tab1_pairs)
        self.tab2 = self.create_crypto_tab("DeFi", self.tab2_pairs)
        self.tab3 = self.create_crypto_tab("Altcoins", self.tab3_pairs)

        self.notebook.add(self.tab1, text="Blue Chips")
        self.notebook.add(self.tab2, text="DeFi")
        self.notebook.add(self.tab3, text="Altcoins")

        # Adicionar notebook ao canvas
        self.canvas_frame = self.canvas.create_window((0,0), 
                                                    window=self.notebook,
                                                    anchor="nw")

        # Configurar eventos de scroll
        self.notebook.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def create_crypto_tab(self, tab_name, pairs):
        tab = tk.Frame(self.notebook, bg='#2c3e50')
        
        for i, symbol in enumerate(pairs):
            crypto_frame = self.create_crypto_frame(tab, symbol)
            row = i // 2
            col = i % 2
            crypto_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
        for i in range(2):
            tab.grid_columnconfigure(i, weight=1)
        
        return tab

    def create_crypto_frame(self, parent, symbol):
        frame = tk.LabelFrame(
            parent,
            text=symbol,
            bg='#2c3e50',
            fg='white',
            font=('Arial', 10, 'bold')
        )

        # Frame para informações da cripto
        info_frame = tk.Frame(frame, bg='#2c3e50')
        info_frame.pack(fill='x', padx=3, pady=2)

        price_label = tk.Label(
            info_frame,
            text="--",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='white'
        )
        price_label.pack(side='left', padx=3)

        change_label = tk.Label(
            info_frame,
            text="--",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='white'
        )
        change_label.pack(side='left', padx=3)

        volume_label = tk.Label(
            info_frame,
            text="Vol: --",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='white'
        )
        volume_label.pack(side='right', padx=3)

        # Frame para gráficos
        charts_frame = tk.Frame(frame, bg='#2c3e50')
        charts_frame.pack(fill='both', expand=True, padx=3, pady=2)

        # Gráfico de preços
        price_fig = Figure(figsize=(4, 1.5), dpi=100, facecolor='#2c3e50')
        price_ax = price_fig.add_subplot(111)
        price_ax.set_facecolor('#2c3e50')
        price_ax.tick_params(colors='white', labelsize=6)
        for spine in price_ax.spines.values():
            spine.set_color('#34495e')
        
        price_canvas = FigureCanvasTkAgg(price_fig, master=charts_frame)
        price_canvas.get_tk_widget().pack(fill='both', expand=True)

        # Gráfico Bull/Bear Power
        bb_fig = Figure(figsize=(4, 0.75), dpi=100, facecolor='#2c3e50')
        bb_ax = bb_fig.add_subplot(111)
        bb_ax.set_facecolor('#2c3e50')
        bb_ax.tick_params(colors='white', labelsize=6)
        for spine in bb_ax.spines.values():
            spine.set_color('#34495e')
        
        bb_canvas = FigureCanvasTkAgg(bb_fig, master=charts_frame)
        bb_canvas.get_tk_widget().pack(fill='both', expand=True)

        # Ajustar margens dos gráficos
        price_fig.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
        bb_fig.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.25)

        # Armazenar referências
        frame.symbol = symbol
        frame.price_label = price_label
        frame.change_label = change_label
        frame.volume_label = volume_label
        frame.price_fig = price_fig
        frame.price_ax = price_ax
        frame.price_canvas = price_canvas
        frame.bb_fig = bb_fig
        frame.bb_ax = bb_ax
        frame.bb_canvas = bb_canvas

        return frame

    def initialize_crypto_data(self):
        all_pairs = self.tab1_pairs + self.tab2_pairs + self.tab3_pairs
        for symbol in all_pairs:
            try:
                # Obter dados históricos
                klines_data = self.get_binance_klines(symbol, interval='1m', limit=self.data_points)
                
                self.crypto_data[symbol] = deque(klines_data, maxlen=self.data_points)
                
                # Calcular Bull/Bear Power inicial
                if klines_data:
                    df = pd.DataFrame(klines_data)
                    ema13 = df['close'].ewm(span=13).mean()
                    bull_power = df['high'] - ema13
                    bear_power = df['low'] - ema13
                    
                    self.bull_bear_data[symbol] = deque(maxlen=self.data_points)
                    for i in range(len(df)):
                        self.bull_bear_data[symbol].append({
                            'timestamp': df['timestamp'].iloc[i],
                            'bull': bull_power.iloc[i],
                            'bear': bear_power.iloc[i]
                        })
            
            except Exception as e:
                print(f"Erro ao inicializar dados para {symbol}: {e}")

    def format_price(self, price):
        """Formata o preço baseado em sua magnitude"""
        if price >= 1000:
            return f"${price:,.2f}"
        elif price >= 1:
            return f"${price:.2f}"
        elif price >= 0.01:
            return f"${price:.4f}"
        else:
            return f"${price:.8f}"

    def format_volume(self, volume):
        """Formata o volume em K, M, B"""
        if volume >= 1_000_000_000:
            return f"{volume/1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"{volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.1f}K"
        else:
            return f"{volume:.0f}"

    def update_crypto_frame(self, frame):
        symbol = frame.symbol
        try:
            # Obter dados mais recentes
            current_data = self.get_binance_klines(symbol, interval='1m', limit=1)
            
            if not current_data:
                return

            # Atualizar dados históricos
            self.crypto_data[symbol].append(current_data[0])

            # Calcular variação 24h
            ticker = self.client.get_ticker(symbol=symbol)
            change_24h = float(ticker['priceChangePercent'])
            last_price = float(ticker['lastPrice'])
            volume_24h = float(ticker['volume'])

            # Atualizar labels
            frame.price_label.config(
                text=self.format_price(last_price),
                fg='white'
            )
            frame.change_label.config(
                text=f"{change_24h:+.2f}%",
                fg='green' if change_24h >= 0 else 'red'
            )
            frame.volume_label.config(
                text=f"Vol: {self.format_volume(volume_24h)}",
                fg='white'
            )

            # Atualizar gráficos
            self.update_charts(frame)

        except Exception as e:
            print(f"Erro ao atualizar {symbol}: {e}")

    def update_charts(self, frame):
        symbol = frame.symbol
        data = list(self.crypto_data[symbol])
        
        if len(data) < 2:
            return
            
        # Atualizar gráfico de preços
        frame.price_ax.clear()
        timestamps = [d['timestamp'] for d in data]
        prices = [d['close'] for d in data]
        
        frame.price_ax.plot(timestamps, prices, color='white', linewidth=1)
        frame.price_ax.set_facecolor('#2c3e50')
        frame.price_ax.tick_params(colors='white', labelsize=6)
        frame.price_ax.grid(True, color='#34495e', linestyle='--', alpha=0.3)
        
        # Atualizar Bull/Bear Power
        frame.bb_ax.clear()
        df = pd.DataFrame(data)
        ema13 = df['close'].ewm(span=13).mean()
        bull_power = df['high'] - ema13
        bear_power = df['low'] - ema13
        
        frame.bb_ax.fill_between(timestamps, bull_power, 0, 
                               where=(bull_power >= 0), 
                               color='green', alpha=0.3)
        frame.bb_ax.fill_between(timestamps, bull_power, 0, 
                               where=(bull_power < 0), 
                               color='red', alpha=0.3)
        frame.bb_ax.fill_between(timestamps, bear_power, 0, 
                               where=(bear_power >= 0), 
                               color='green', alpha=0.3)
        frame.bb_ax.fill_between(timestamps, bear_power, 0, 
                               where=(bear_power < 0), 
                               color='red', alpha=0.3)
        
        frame.bb_ax.set_facecolor('#2c3e50')
        frame.bb_ax.tick_params(colors='white', labelsize=6)
        frame.bb_ax.grid(True, color='#34495e', linestyle='--', alpha=0.3)
        
        # Atualizar canvas
        frame.price_canvas.draw()
        frame.bb_canvas.draw()

    def update_market_info(self):
        """Atualiza informações gerais do mercado"""
        try:
            # Obter dados do Bitcoin para dominância
            btc_ticker = self.client.get_ticker(symbol='BTCUSDT')
            btc_price = float(btc_ticker['lastPrice'])
            btc_market_cap = btc_price * 19_000_000  # Aproximado

            # Atualizar labels
            self.btc_dominance_label.config(
                text=f"BTC: ${btc_price:,.0f}"
            )
            self.market_cap_label.config(
                text=f"BTC MCap: ${btc_market_cap/1_000_000_000:.0f}B"
            )
        except Exception as e:
            print(f"Erro ao atualizar informações do mercado: {e}")

    def update_current_tab(self):
        current_tab = self.notebook.select()
        tab_index = self.notebook.index(current_tab)
        
        if tab_index == 0:
            pairs = self.tab1_pairs
            tab = self.tab1
        elif tab_index == 1:
            pairs = self.tab2_pairs
            tab = self.tab2
        else:
            pairs = self.tab3_pairs
            tab = self.tab3

        for widget in tab.winfo_children():
            if isinstance(widget, tk.LabelFrame) and hasattr(widget, 'symbol'):
                self.update_crypto_frame(widget)

    def update_loop(self):
        while True:
            try:
                # Atualizar relógio
                utc_time = datetime.datetime.now(pytz.UTC)
                self.clock_label.config(text=utc_time.strftime('%H:%M:%S UTC'))

                # Atualizar informações do mercado a cada minuto
                if utc_time.second == 0:
                    self.update_market_info()
                    self.update_current_tab()

                time.sleep(1)

            except Exception as e:
                print(f"Erro no loop de atualização: {e}")
                time.sleep(1)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CryptoMonitor(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro na aplicação: {e}")
        input("Pressione Enter para sair...")                    