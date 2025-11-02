import tkinter as tk
from tkinter import font
from tkinter import ttk
import io
import os
import ctypes
import urllib.request
from PIL import Image, ImageTk

from gui.gui_automato import EditorGUI
from gui.gui_mealy import MealyGUI
from gui.gui_moore import MooreGUI
from gui.gui_pilha import PilhaGUI
from gui.gui_turing import TuringGUI
import sv_ttk

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("IC-Tômato++")
        self.root.geometry("500x750")
        
        self.root.eval('tk::PlaceWindow . center')

        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(expand=True)

        self.load_logo()

        title_font = font.Font(family="Helvetica", size=28, weight="bold")
        subtitle_font = font.Font(family="Helvetica", size=16, weight="bold")

        title_canvas = tk.Canvas(main_frame, height=60, bg=main_frame.cget('bg'), highlightthickness=0)
        title_canvas.pack(pady=(0, 5))

        glow_color = "#ffc107"
        for i in range(1, 3):
            title_canvas.create_text(200 - i, 30 - i, text="IC-Tômato++", font=title_font, fill=glow_color, anchor='center')
            title_canvas.create_text(200 + i, 30 + i, text="IC-Tômato++", font=title_font, fill=glow_color, anchor='center')

        title_canvas.create_text(200, 30, text="IC-Tômato++", font=title_font, fill="white", anchor='center')

        label = ttk.Label(main_frame, text="Selecione o Editor", font=subtitle_font)
        label.pack(pady=(0, 25))

        self.create_menu_option(
            main_frame,
            text="Editor de Autômatos Finitos",
            command=self.launch_automaton_editor
        )

        self.create_menu_option(
            main_frame,
            text="Editor de Máquinas de Mealy",
            command=self.launch_mealy_editor
        )

        self.create_menu_option(
            main_frame,
            text="Editor de Máquinas de Moore",
            command=self.launch_moore_editor
        )

        self.create_menu_option(
            main_frame,
            text="Editor de Autômatos de Pilha",
            command=self.launch_pda_editor
        )
        
        self.create_menu_option(
            main_frame,
            text="Editor de Máquinas de Turing",
            command=self.launch_turing_editor
        )

    def create_menu_option(self, parent, text, command):
        """Cria um botão customizado com efeito de hover."""
        NORMAL_BG = "#ffc107"
        HOVER_BG = "#007bff"
        NORMAL_FG = "#212529"
        HOVER_FG = "white"

        frame = tk.Frame(parent, bg=NORMAL_BG)
        frame.pack(pady=10, fill='x')

        label = tk.Label(frame, text=text, bg=NORMAL_BG, fg=NORMAL_FG,
                         font=("Helvetica", 12, "bold"), pady=25, cursor="hand2")
        label.pack(fill='x')

        frame.bind("<Enter>", lambda e: (frame.config(bg=HOVER_BG), label.config(bg=HOVER_BG, fg=HOVER_FG)))
        frame.bind("<Leave>", lambda e: (frame.config(bg=NORMAL_BG), label.config(bg=NORMAL_BG, fg=NORMAL_FG)))
        
        frame.bind("<Button-1>", lambda e: command())
        label.bind("<Button-1>", lambda e: command())

    def launch_automaton_editor(self):
        """Cria uma nova janela (Toplevel) para o editor de autômatos."""
        self.open_editor_window(EditorGUI)

    def launch_mealy_editor(self):
        """Cria uma nova janela (Toplevel) para o editor de Mealy."""
        self.open_editor_window(MealyGUI)

    def launch_moore_editor(self):
        """Cria uma nova janela para o editor de Moore."""
        self.open_editor_window(MooreGUI)

    def launch_pda_editor(self):
        """Cria uma nova janela para o editor de Autômatos de Pilha."""
        self.open_editor_window(PilhaGUI)

    def launch_turing_editor(self):
        """Cria uma nova janela para o editor de Máquinas de Turing."""
        self.open_editor_window(TuringGUI)

    def load_logo(self):
        """Carrega e exibe o logo no canto superior direito."""
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "icon.ico")
        try:
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                display_img = image.resize((80, 80), Image.Resampling.LANCZOS)
                icon_img = image.resize((32, 32), Image.Resampling.LANCZOS)

                self.logo_image = ImageTk.PhotoImage(display_img)
                self.icon_image = ImageTk.PhotoImage(icon_img)

                try:
                    self.root.iconbitmap(icon_path)
                except Exception:
                    try:
                        self.root.iconphoto(False, self.icon_image)
                    except Exception:
                        pass

                logo_label = tk.Label(self.root, image=self.logo_image, bg=self.root.cget('bg'))
                logo_label.place(relx=1.0, y=10, x=-10, anchor='ne')
                self.icon_path = icon_path
                return

            url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_Iz4iLTCkvEbHl93acer5aym3CcSl5CHMBg&s"
            with urllib.request.urlopen(url) as response:
                image_data = response.read()
            image = Image.open(io.BytesIO(image_data))
            display_img = image.resize((80, 80), Image.Resampling.LANCZOS)
            icon_img = image.resize((32, 32), Image.Resampling.LANCZOS)

            self.logo_image = ImageTk.PhotoImage(display_img)
            self.icon_image = ImageTk.PhotoImage(icon_img)
            try:
                self.root.iconphoto(False, self.icon_image)
            except Exception:
                pass
            logo_label = tk.Label(self.root, image=self.logo_image, bg=self.root.cget('bg'))
            logo_label.place(relx=1.0, y=10, x=-10, anchor='ne')
            self.icon_path = None

        except Exception as e:
            print(f"Não foi possível carregar o logo: {e}")

    def open_editor_window(self, EditorClass):
        """Oculta o menu principal e abre o editor passado como classe.

        Ao fechar a janela do editor, o menu principal é restaurado.
        """
        try:
            self.root.withdraw()
        except Exception:
            pass

        editor_window = tk.Toplevel(self.root)
        try:
            if hasattr(self, 'icon_path') and self.icon_path:
                try:
                    editor_window.iconbitmap(self.icon_path)
                except Exception:
                    if hasattr(self, 'icon_image'):
                        editor_window.iconphoto(False, self.icon_image)
            else:
                if hasattr(self, 'icon_image'):
                    editor_window.iconphoto(False, self.icon_image)
        except Exception:
            pass
        editor_app = EditorClass(editor_window)

        def on_close():
            try:
                editor_window.destroy()
            except Exception:
                pass
            try:
                self.root.deiconify()
            except Exception:
                pass

        editor_window.protocol("WM_DELETE_WINDOW", on_close)

def main():
    root = tk.Tk()

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    sv_ttk.set_theme("light")
    
    app = MainMenu(root)
    root.mainloop()

if __name__ == "__main__":
    main()