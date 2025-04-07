import os
import wave
import time
import threading
import random
import tkinter as tk
import pyaudio
import speech_recognition as sr
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from audio_manage import procesar_audio, guardar_audio
from scipy.signal import firwin, lfilter, butter

class VoiceRecorder:
    def __init__(self):
        self.OUTPUT_FILENAME = r"grabacion.wav"
        self.OUTPUT_FILENAME_FILT = r"grabacion_filtrada.wav"
        self.selected_filter = ""
        #sample_rate, tiempo, audio_data, audio_data_db
        self.audio_sr = 0.0
        self.audio_time = 0.0
        self.audio_audiodata = []
        self.audio_audiodata_db = []
        self.filtered_audio_audiodata = []
        self.audio_text = ""
        self.recording = False
        self.playback_speed = 1.0  # Velocidad de reproducción normal por defecto
        self.is_playing = False

        self.root = tk.Tk()
        self.root.title("Grabador de voz inteligente")
        self.root.geometry("720x600")
        #self.root.resizable(False, False)

        ##### BOTONES #####
        self.button = tk.Button(text = "Grabar",
                                     font = ("Arial", 10, "bold"),
                                     command = self.click_handler)
        self.button_totext = tk.Button(text = "Sí",
                                     font = ("Arial", 10, "bold"),
                                     command = self.to_text)
        self.button_filter_list = tk.Button(text = "Seleccionar",
                                     font = ("Arial", 10, "bold"),
                                     command = self.select_filter)

        ##### ETIQUETAS #####
        self.label = tk.Label(text = "00:00:00",
                              font = ("Arial",15))
        self.label_quest = tk.Label(text = "",
                                    font = ("Arial", 15))
        self.label_quest_typefilter = tk.Label(text = "",
                                    font = ("Arial", 15))
        self.label_welcome = tk.Label(text = "Bienvenid@ al grabador de audio inteligente",
                                      font = ("Arial", 25))
        self.label_head_record = tk.Label(text = "Grabación de audio",
                                      font = ("Arial", 20))
        self.label_head_totext = tk.Label(text = "Audio a texto",
                                      font = ("Arial", 20))
        self.label_head_filters = tk.Label(text = "Aplica filtros",
                                      font = ("Arial", 20))
        self.label_config_filter = tk.Label(text = "Configura tu filtro",
                                    font = ("Arial", 15))

        ##### ENTRADAS TEXTO #####
        self.text_output = tk.Text(height=5,
                                   width=30,
                                   font=("Arial", 13))

        ##### LIST BOXES #####
        self.filter_list = tk.Listbox(height=2)
        self.filter_list.insert(1, "IIR")
        self.filter_list.insert(2, "FIR")

        # Configurar las columnas para que ocupen el espacio disponible
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Colocar los widgets usando grid
        self.label_welcome.grid(row=0, column=0, columnspan=2, padx=2, pady=(10, 30), sticky='ew')

        self.label_head_record.grid(row=1, column=0)
        self.label.grid(row=2, column=0)
        self.button.grid(row=3, column=0)

        self.label_head_filters.grid(row=4, column=0, pady=(25,5), sticky='ew', columnspan=2)
        self.label_quest_typefilter.grid(row=5, column=0)

        self.label_head_totext.grid(row=1, column=1)
        self.label_quest.grid(row=2,column=1)

        self.root.mainloop()

    def show_filtlen(self,filtlen):
        self.label_filtlen.config(text=f" Longitud de filtro: [{filtlen}] ")

    def show_cutfreq(self,cutfreq):
        self.label_cutfreq.config(text=f"Frecuencia de corte: [{cutfreq}]")

    def show_filtorder(self,filtorder):
        self.label_filtorder.config(text=f"   Orden de filtro: [{filtorder}]   ")

    def apply_filter(self):
        frec_corte = self.scale_cutfreq.get()  # Frecuencia de corte en Hz
        tasa_muestreo = self.audio_sr

        if self.selected_filter == "FIR":
            # Parámetros del filtro FIR
            longitud_filtro = self.scale_filtlen.get()  # Longitud del filtro FIR (número impar)
            pass_z = True
            if(self.list_pass.get(self.list_pass.curselection()))=="Pasa altos":
                pass_z = False

            # Diseñar el filtro FIR
            coeficientes_filtro = firwin(longitud_filtro, frec_corte / (tasa_muestreo / 2), pass_zero=pass_z)

            # Aplicar el filtro FIR a la señal de entrada
            self.filtered_audio_audiodata = lfilter(coeficientes_filtro, 1.0, self.audio_audiodata)

        elif self.selected_filter == "IIR":
            # Parámetros del filtro IIR
            orden_filtro = self.scale_filtorder.get()
            btype = "low"
            if(self.list_pass.get(self.list_pass.curselection()))=="Pasa altos":
                btype = "high"
            # Diseñar el filtro IIR pasa bajo
            b, a = butter(orden_filtro, frec_corte, btype=btype, analog=False, fs=tasa_muestreo)

            # Aplicar el filtro IIR a la señal de entrada
            self.filtered_audio_audiodata = lfilter(b, a, self.audio_audiodata)

        # Guardar el audio filtrado
        print("Audio filtrado guardado")
        guardar_audio(self.OUTPUT_FILENAME_FILT, tasa_muestreo, self.filtered_audio_audiodata)

        self.show_audio_window()

    def select_filter(self):
        filter_selected = self.filter_list.curselection()
        text_selected = self.filter_list.get(filter_selected)

        self.audio_sr, self.audio_time, self.audio_audiodata, self.audio_audiodata_db = procesar_audio(self.OUTPUT_FILENAME)

        sample_rate = self.audio_sr  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< PENDIENTE POR DEFINIR

        # SECCIÓN DE CONFIGURACIÓN DE FILTROS
        self.label_filtlen = tk.Label(text=" Longitud de filtro: [-] ", font=("Arial", 10))
        self.label_cutfreq = tk.Label(text="Frecuencia de corte: [-]", font=("Arial", 10))
        self.label_pass = tk.Label(text="Filtro pasa:", font=("Arial", 10))
        self.label_filtorder = tk.Label(text="   Orden de filtro: [-]   ", font=("Arial", 10))

        self.scale_filtlen = tk.Scale(from_=1, to=100, orient="horizontal", command=self.show_filtlen)
        self.scale_cutfreq = tk.Scale(from_=0, to=(sample_rate/2), orient="horizontal", command=self.show_cutfreq)
        self.scale_filtorder = tk.Scale(from_=1, to=10, orient="horizontal", command=self.show_filtorder)
        self.list_pass = tk.Listbox(height=2)
        self.list_pass.insert(0, "Pasa bajos")
        self.list_pass.insert(1, "Pasa altos")

        self.label_confirm_filter = tk.Label(text="Confirmar selección y filtrar", font=("Arial", 11))
        self.button_confirm_filter = tk.Button(text="Filtrar audio", font=("Arial", 10, "bold"), command=self.apply_filter)

        # Colocar todos los widgets inicialmente en la cuadrícula (aunque algunos serán ocultados luego)
        self.label_filtlen.grid(row=6, column=1)
        self.scale_filtlen.grid(row=7, column=1)
        self.label_filtorder.grid(row=6, column=1)
        self.scale_filtorder.grid(row=7, column=1)
        self.label_cutfreq.grid(row=8, column=1)
        self.scale_cutfreq.grid(row=9, column=1)
        self.label_pass.grid(row=10, column=1)
        self.list_pass.grid(row=11, column=1)

        # Ocultar widgets según el filtro seleccionado
        if text_selected == "IIR":  # IIR
            self.selected_filter = "IIR"
            self.label_config_filter.config(text="Configura tu filtro IIR:")
            self.label_config_filter.grid(row=5, column=1)

            # Ocultar los widgets de FIR
            self.label_filtlen.grid_forget()
            self.scale_filtlen.grid_forget()

            # Mostrar los widgets de IIR
            self.label_filtorder.grid(row=6, column=1)
            self.scale_filtorder.grid(row=7, column=1)

        elif text_selected == "FIR":  # FIR
            self.selected_filter = "FIR"
            self.label_config_filter.config(text="Configura tu filtro FIR:")
            self.label_config_filter.grid(row=5, column=1)

            # Ocultar los widgets de IIR
            self.label_filtorder.grid_forget()
            self.scale_filtorder.grid_forget()

            # Mostrar los widgets de FIRprint("FIR")
            self.label_filtlen.grid(row=6, column=1)
            self.scale_filtlen.grid(row=7, column=1)

        self.label_confirm_filter.grid(row=12, column=1)
        self.button_confirm_filter.grid(row=13, column=1)

    def to_text(self):
        self.button_totext.grid_forget()
        self.text_output.delete(1.0, tk.END)
        self.label_quest.config(text="Procesando audio...")
        time.sleep(2)
        # Procesa el audio para obtener texto
        recognizer = sr.Recognizer()
        with sr.AudioFile(self.OUTPUT_FILENAME) as source:
            audio_data = recognizer.record(source)
            try:
                self.audio_text = recognizer.recognize_google(audio_data, language='es-ES')
                self.label_quest.config(text="Texto reconocido:")
                self.text_output.insert(1.0, self.audio_text)
                self.text_output.grid(row=3, column=1)
                print("Texto reconocido:", self.audio_text)
            except sr.UnknownValueError:
                self.label_quest.config(text="No se pudo entender el audio")
                print("No se pudo entender el audio.")
            except sr.RequestError as e:
                self.label_quest.config(text=f"ERROR: {e}")
                print(f"Error en el servicio de reconocimiento: {e}")

    def click_handler(self):
        if self.recording:
            self.recording = False
            self.button.config(fg="black", text="Grabar")  # Cambia el texto del botón
            self.label.config(fg="black")
        else:
            self.recording = True
            self.button.config(fg="black", text="Finalizar")  # Actualiza el texto cuando graba
            self.label.config(fg="red")
            self.text_output.grid_forget()
            threading.Thread(target=self.record).start()

    def record(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 5

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Grabando...")
        frames = []

        start = time.time()

        while self.recording:
            data = stream.read(CHUNK)
            frames.append(data)

            passed = time.time() - start
            secs = passed % 60
            mins = passed // 60
            hours = mins // 60
            self.label.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}")

        stream.stop_stream()
        stream.close()
        audio.terminate()

        color_quest = ["#e67e22", "#3498db", "#2ecc71"]
        # Guarda los datos de audio en un archivo WAV
        try:
            # Guarda los datos de audio en un archivo WAV
            with wave.open(self.OUTPUT_FILENAME, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            print(f"Audio guardado como '{self.OUTPUT_FILENAME}'")
            color = random.choice(color_quest)
            self.label_quest.config(text="¿Quieres pasar el audio a texto?",
                                    fg = color)
            self.button_totext.config(bg = color)
            self.button_totext.grid(row=3,column=1)

            self.label_quest_typefilter.config(text="¿Quieres aplicar algún filtro?\nSelecciónalo:", fg = color)
            self.filter_list.grid(row=6, column=0)
            self.button_filter_list.config(bg = color)
            self.button_filter_list.grid(row=7,column=0)
        except Exception as e:
            print(f"Error al guardar el archivo WAV: {e}")

    def show_audio_window(self):
        # Nueva ventana para reproducir audio y mostrar gráficas
        audio_window = tk.Toplevel(self.root)
        audio_window.title("Reproducir Audio y Ver Gráficas")
        audio_window.geometry("800x700")

        # Frame para controles de reproducción
        playback_frame = tk.Frame(audio_window)
        playback_frame.pack(pady=10)

        # Frame para controles de velocidad
        speed_frame = tk.Frame(audio_window)
        speed_frame.pack(pady=10)

        # Etiqueta y slider para control de velocidad
        self.label_playback_speed = tk.Label(speed_frame, text="Velocidad de reproducción: 1.0x", font=("Arial", 10))
        self.label_playback_speed.pack()

        self.speed_slider = tk.Scale(speed_frame, from_=0.5, to=2.0, resolution=0.1, orient="horizontal",
                                    command=self.update_playback_speed)
        self.speed_slider.set(1.0)
        self.speed_slider.pack()

        # Crear botones para reproducir audio
        play_original_button = tk.Button(playback_frame, text="Reproducir Audio Original", 
                                       command=lambda: threading.Thread(target=self.play_original_audio).start())
        play_filtered_button = tk.Button(playback_frame, text="Reproducir Audio Filtrado", 
                                        command=lambda: threading.Thread(target=self.play_filtered_audio).start())
        
        play_original_button.pack(side=tk.LEFT, padx=10)
        play_filtered_button.pack(side=tk.LEFT, padx=10)

        # Crear gráficas para mostrar las señales de audio
        self.plot_audio_graphs(audio_window)

    def update_playback_speed(self, val):
        self.playback_speed = float(val)
        self.label_playback_speed.config(text=f"Velocidad de reproducción: {self.playback_speed:.1f}x")

    def play_original_audio(self):
        self.play_audio(self.OUTPUT_FILENAME)

    def play_filtered_audio(self):
        self.play_audio(self.OUTPUT_FILENAME_FILT)

    def play_audio(self, filename):
        if self.is_playing:
            return
            
        self.is_playing = True
        
        try:
            wf = wave.open(filename, 'rb')
            p = pyaudio.PyAudio()
            
            # Calcular el rate ajustado según la velocidad de reproducción
            original_rate = wf.getframerate()
            adjusted_rate = int(original_rate * self.playback_speed)
            
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                           channels=wf.getnchannels(),
                           rate=adjusted_rate,
                           output=True)

            data = wf.readframes(1024)
            while data and self.is_playing:
                stream.write(data)
                data = wf.readframes(1024)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
        except Exception as e:
            print(f"Error al reproducir audio: {e}")
        finally:
            self.is_playing = False

    def plot_audio_graphs(self, parent_window):
        # Crear gráficas para la señal original y filtrada
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

        # Definir el tiempo en función de la longitud de la señal
        tiempo = self.audio_time

        # Gráfico del audio original
        ax1.plot(tiempo, self.audio_audiodata, label='Señal de Entrada')
        ax1.set_title('Señal de Entrada')
        ax1.set_xlabel('Tiempo (s)')
        ax1.set_ylabel('Amplitud')
        ax1.legend()

        # Gráfico del audio filtrado (si está disponible)
        if hasattr(self, 'filtered_audio_audiodata') and len(self.filtered_audio_audiodata) > 0:
            ax2.plot(tiempo, self.filtered_audio_audiodata, label='Señal Filtrada', color='orange')
            ax2.set_title('Señal Filtrada')
            ax2.set_xlabel('Tiempo (s)')
            ax2.set_ylabel('Amplitud')
            ax2.legend()
        else:
            ax2.plot([])  # Si no hay audio filtrado, muestra un gráfico vacío
            ax2.set_title('Señal Filtrada (no disponible)')
            ax2.set_xlabel('Tiempo (s)')
            ax2.set_ylabel('Amplitud')

        plt.tight_layout()

        # Convertir el gráfico en un lienzo de tkinter y colocarlo en la ventana
        canvas = FigureCanvasTkAgg(fig, master=parent_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

VoiceRecorder()
