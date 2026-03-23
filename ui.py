"""
Interface utilisateur graphique pour le générateur de tests unitaires avec Ollama
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import os
import sys
from pathlib import Path
import time
import logging


class TestGeneratorUI:
    """Interface utilisateur pour le générateur de tests"""

    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Tests Unitaires - Ollama")
        self.root.geometry("1200x800")
        
        # Variables pour les paramètres
        self.setup_variables()
        
        # Suivi des logs (initialisation avant l'UI)
        self.log_file_path = "unit_test_generator.log"
        self.log_position = 0
        self.check_logs_running = False
        
        # Interface utilisateur
        self.setup_ui()
        
    def setup_variables(self):
        """Initialise les variables tkinter pour tous les paramètres"""
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar(value="")
        self.model = tk.StringVar(value="llama3:8b")
        self.host = tk.StringVar(value="localhost:11434")
        self.exclude_dirs = tk.StringVar(value="__pycache__, .git, venv, env, .venv")
        self.exclude_files = tk.StringVar(value="__init__.py, setup.py")
        self.verbose = tk.BooleanVar()
        self.dry_run = tk.BooleanVar()
        self.no_minimal_processing = tk.BooleanVar()
        self.create_venv = tk.BooleanVar()
        self.os_type = tk.StringVar(value="auto")
        
        # Variable pour l'état de la génération
        self.generation_running = tk.BooleanVar(value=False)
        
        # Callback pour mettre à jour automatiquement le répertoire de sortie
        self.source_dir.trace_add('write', self.on_source_dir_changed)
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Configuration du style
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Section.TLabel', font=('Arial', 10, 'bold'))
        
        # Frame principal avec scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Titre
        title_label = ttk.Label(
            scrollable_frame, 
            text="Générateur de Tests Unitaires avec Ollama", 
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Configuration de la grille
        scrollable_frame.columnconfigure(1, weight=1)
        
        row = 1
        
        # Section: Chemins et fichiers
        row = self.add_section_title(scrollable_frame, "Chemins et fichiers", row)
        row = self.add_path_field(scrollable_frame, "Répertoire source:", self.source_dir, row, True)
        row = self.add_path_field(scrollable_frame, "Répertoire de sortie:", self.output_dir, row, False)
        
        # Section: Configuration Ollama
        row = self.add_section_title(scrollable_frame, "Configuration Ollama", row)
        row = self.add_text_field(scrollable_frame, "Modèle:", self.model, row)
        row = self.add_text_field(scrollable_frame, "Hôte:", self.host, row)
        
        # Section: Exclusions
        row = self.add_section_title(scrollable_frame, "Exclusions", row)
        row = self.add_text_field(
            scrollable_frame, 
            "Répertoires à exclure:", 
            self.exclude_dirs, 
            row,
            tooltip="Séparez par des virgules"
        )
        row = self.add_text_field(
            scrollable_frame, 
            "Fichiers à exclure:", 
            self.exclude_files, 
            row,
            tooltip="Séparez par des virgules"
        )
        
        # Section: Options
        row = self.add_section_title(scrollable_frame, "Options", row)
        row = self.add_checkbox(scrollable_frame, "Mode verbose", self.verbose, row)
        row = self.add_checkbox(scrollable_frame, "Mode simulation (dry-run)", self.dry_run, row)
        row = self.add_checkbox(
            scrollable_frame, 
            "Désactiver le traitement minimal", 
            self.no_minimal_processing, 
            row,
            tooltip="Peut introduire des erreurs de syntaxe"
        )
        row = self.add_checkbox(scrollable_frame, "Créer environnement virtuel", self.create_venv, row)
        
        # Type d'OS
        row = self.add_combobox(
            scrollable_frame, 
            "Type d'OS:", 
            self.os_type, 
            ["auto", "windows", "linux"], 
            row
        )
        
        # Boutons
        row = self.add_buttons(scrollable_frame, row)
        
        # Zone de statut
        row = self.add_status_section(scrollable_frame, row)
        
        # Configuration du canvas
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Zone de logs (en bas de la fenêtre principale)
        self.add_log_section()
        
    def add_section_title(self, parent, title, row):
        """Ajoute un titre de section"""
        ttk.Separator(parent, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 5)
        )
        row += 1
        
        label = ttk.Label(parent, text=title, style='Section.TLabel')
        label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        return row + 1
    
    def add_text_field(self, parent, label_text, variable, row, tooltip=None):
        """Ajoute un champ de texte"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=(10, 5), pady=2)
        
        entry = ttk.Entry(parent, textvariable=variable, width=50)
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=2)
        
        if tooltip:
            self.create_tooltip(entry, tooltip)
            
        return row + 1
    
    def add_path_field(self, parent, label_text, variable, row, is_directory=True):
        """Ajoute un champ avec bouton de sélection de chemin"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=(10, 5), pady=2)
        
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=2)
        frame.columnconfigure(0, weight=1)
        
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        def browse_path():
            if is_directory:
                path = filedialog.askdirectory(initialdir=variable.get() or ".")
            else:
                path = filedialog.askdirectory(initialdir=variable.get() or ".")
                
            if path:
                variable.set(path)
        
        browse_btn = ttk.Button(frame, text="Parcourir", command=browse_path)
        browse_btn.grid(row=0, column=1)
        
        return row + 1
    
    def add_checkbox(self, parent, label_text, variable, row, tooltip=None):
        """Ajoute une checkbox"""
        checkbox = ttk.Checkbutton(parent, text=label_text, variable=variable)
        checkbox.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        if tooltip:
            self.create_tooltip(checkbox, tooltip)
            
        return row + 1
    
    def add_combobox(self, parent, label_text, variable, values, row):
        """Ajoute une combobox"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=(10, 5), pady=2)
        
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=2)
        
        return row + 1
    
    def add_buttons(self, parent, row):
        """Ajoute les boutons d'action"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        # Bouton génération
        self.generate_btn = ttk.Button(
            button_frame, 
            text="Générer les tests", 
            command=self.start_generation,
            style='Accent.TButton'
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton stop
        self.stop_btn = ttk.Button(
            button_frame, 
            text="Arrêter", 
            command=self.stop_generation,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton effacer logs
        clear_log_btn = ttk.Button(
            button_frame, 
            text="Effacer logs", 
            command=self.clear_logs
        )
        clear_log_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton test logs
        test_log_btn = ttk.Button(
            button_frame, 
            text="Test logs", 
            command=self.test_logs
        )
        test_log_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton aide
        help_btn = ttk.Button(button_frame, text="Aide", command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        return row + 1
    
    def add_status_section(self, parent, row):
        """Ajoute la section de statut"""
        status_frame = ttk.LabelFrame(parent, text="Statut", padding=10)
        status_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Prêt")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Indicateur de surveillance des logs
        self.log_status_label = ttk.Label(status_frame, text="📄 Logs: En attente", foreground="orange")
        self.log_status_label.grid(row=1, column=0, sticky="w")
        
        # Barre de progression
        self.progress_var = tk.StringVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            mode='indeterminate',
            length=200
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        return row + 1
    
    def add_log_section(self):
        """Ajoute la zone de logs en bas de la fenêtre"""
        # Frame séparé pour les logs
        log_frame = ttk.LabelFrame(self.root, text="Logs en temps réel", padding=5)
        log_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))
        
        # Zone de texte avec scrollbar
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=150, 
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Configuration des couleurs pour différents niveaux de log
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("INFO", foreground="blue")
        self.log_text.tag_configure("DEBUG", foreground="gray")
        
        # Démarrage de la surveillance des logs
        self.start_log_monitoring()
    
    def create_tooltip(self, widget, text):
        """Crée une tooltip pour un widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow")
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def start_generation(self):
        """Démarre la génération des tests"""
        # Validation des champs obligatoires
        if not self.source_dir.get().strip():
            messagebox.showerror("Erreur", "Le répertoire source est obligatoire")
            return
        
        if not os.path.exists(self.source_dir.get().strip()):
            messagebox.showerror("Erreur", "Le répertoire source n'existe pas")
            return
        
        # Construction de la commande
        command = self.build_command()
        
        # Interface
        self.generation_running.set(True)
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.start(10)
        self.status_label.config(text="Génération en cours...")
        
        # Démarrage du thread
        self.generation_thread = threading.Thread(
            target=self.run_generation, 
            args=(command,),
            daemon=True
        )
        self.generation_thread.start()
    
    def stop_generation(self):
        """Arrête la génération"""
        if hasattr(self, 'process') and self.process:
            self.process.terminate()
        
        self.generation_running.set(False)
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.status_label.config(text="Arrêté par l'utilisateur")
    
    def build_command(self):
        """Construit la commande à exécuter"""
        script_path = Path(__file__).parent / "run.py"
        command = [sys.executable, str(script_path)]
        
        # Répertoire source (obligatoire)
        command.append(self.source_dir.get().strip())
        
        # Paramètres optionnels
        output_dir = self.get_output_dir()
        # Toujours passer le répertoire de sortie pour être sûr
        command.extend(["--output-dir", output_dir])
            
        if self.model.get().strip() != "llama3:8b":
            command.extend(["--model", self.model.get().strip()])
            
        if self.host.get().strip() != "localhost:11434":
            command.extend(["--host", self.host.get().strip()])
        
        # Exclusions
        if self.exclude_dirs.get().strip():
            dirs = [d.strip() for d in self.exclude_dirs.get().split(",") if d.strip()]
            if dirs:
                command.extend(["--exclude-dirs"] + dirs)
                
        if self.exclude_files.get().strip():
            files = [f.strip() for f in self.exclude_files.get().split(",") if f.strip()]
            if files:
                command.extend(["--exclude-files"] + files)
        
        # Options booléennes
        if self.verbose.get():
            command.append("--verbose")
        if self.dry_run.get():
            command.append("--dry-run")
        if self.no_minimal_processing.get():
            command.append("--no-minimal-processing")
        if self.create_venv.get():
            command.append("--create-venv")
            
        if self.os_type.get() != "auto":
            command.extend(["--os-type", self.os_type.get()])
        
        return command
    
    def run_generation(self, command):
        """Exécute la génération dans un thread séparé"""
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Lecture de la sortie en temps réel
            for line in iter(self.process.stdout.readline, ''):
                if not self.generation_running.get():
                    break
                # Les logs sont déjà écrits dans le fichier par run.py
                # On peut afficher la progression ici si nécessaire
                
            self.process.wait()
            return_code = self.process.returncode
            
            # Mise à jour de l'interface dans le thread principal
            self.root.after(100, lambda: self.generation_completed(return_code))
            
        except Exception as e:
            self.root.after(100, lambda: self.generation_error(str(e)))
        finally:
            self.process = None
    
    def generation_completed(self, return_code):
        """Appelé quand la génération est terminée"""
        self.generation_running.set(False)
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        
        if return_code == 0:
            self.status_label.config(text="Génération terminée avec succès")
            messagebox.showinfo("Succès", "Génération des tests terminée avec succès!")
        else:
            self.status_label.config(text=f"Génération échouée (code: {return_code})")
            messagebox.showerror("Erreur", f"Génération échouée avec le code: {return_code}")
    
    def generation_error(self, error_message):
        """Appelé en cas d'erreur durant la génération"""
        self.generation_running.set(False)
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.status_label.config(text="Erreur durant la génération")
        messagebox.showerror("Erreur", f"Erreur durant la génération:\n{error_message}")
    
    def start_log_monitoring(self):
        """Démarre la surveillance du fichier de log"""
        if not self.check_logs_running:
            self.check_logs_running = True
            # Initialiser la position de lecture au début ou à la fin du fichier existant
            if os.path.exists(self.log_file_path):
                try:
                    self.log_position = os.path.getsize(self.log_file_path)
                    self.display_log_content(f"[UI] Surveillance des logs démarrée - fichier existant ({self.log_position} bytes)\n")
                    self.log_status_label.config(text="📄 Logs: ✓ Surveillance active", foreground="green")
                except Exception:
                    self.log_position = 0
            else:
                self.log_position = 0
                self.display_log_content("[UI] Surveillance des logs démarrée - en attente du fichier de log\n")
                self.log_status_label.config(text="📄 Logs: ⏳ En attente fichier", foreground="orange")
            
            self.check_logs()
    
    def check_logs(self):
        """Vérifie les nouveaux logs et les affiche"""
        try:
            if os.path.exists(self.log_file_path):
                current_size = os.path.getsize(self.log_file_path)
                
                # Mettre à jour l'indicateur visuel
                if hasattr(self, 'log_status_label'):
                    self.log_status_label.config(text="📄 Logs: ✓ Surveillance active", foreground="green")
                
                # Vérifier si le fichier a été tronqué (nouveau run)
                if current_size < self.log_position:
                    self.log_position = 0
                    self.display_log_content("[UI] Nouveau fichier de log détecté\n")
                
                # Lire seulement s'il y a du nouveau contenu
                if current_size > self.log_position:
                    with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(self.log_position)
                        new_content = f.read()
                        
                        if new_content.strip():  # Ignorer les lignes vides
                            self.log_position = f.tell()
                            self.display_log_content(new_content)
            else:
                # Fichier n'existe pas encore
                if hasattr(self, 'log_status_label'):
                    self.log_status_label.config(text="📄 Logs: ⏳ En attente fichier", foreground="orange")
                            
        except Exception as e:
            # Afficher l'erreur dans les logs pour diagnostiquer
            error_msg = f"[UI ERROR] Erreur lecture logs: {str(e)}\n"
            self.display_log_content(error_msg)
            if hasattr(self, 'log_status_label'):
                self.log_status_label.config(text="📄 Logs: ✗ Erreur lecture", foreground="red")
        
        # Programmation de la prochaine vérification
        if self.check_logs_running:
            self.root.after(200, self.check_logs)  # Vérification plus fréquente (200ms)
    
    def display_log_content(self, content):
        """Affiche le contenu des logs dans la zone de texte"""
        self.log_text.config(state=tk.NORMAL)
        
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                # Détection du niveau de log améliorée
                tag = "INFO"  # Par défaut INFO
                line_upper = line.upper()
                
                if "ERROR" in line_upper:
                    tag = "ERROR"
                elif "WARNING" in line_upper or "WARN" in line_upper:
                    tag = "WARNING"
                elif "DEBUG" in line_upper:
                    tag = "DEBUG"
                elif "INFO" in line_upper:
                    tag = "INFO"
                # Garde INFO comme défaut pour toutes les autres lignes
                
                self.log_text.insert(tk.END, line + '\n', tag)
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)  # Scroll vers le bas
    
    def clear_logs(self):
        """Efface la zone de logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Remet à zéro la position de lecture du fichier
        self.log_position = 0
        if os.path.exists(self.log_file_path):
            try:
                self.log_position = os.path.getsize(self.log_file_path)
            except Exception:
                self.log_position = 0
        
        # Message de confirmation
        self.display_log_content("[UI] Zone de logs effacée\n")
    
    def test_logs(self):
        """Test et diagnostic du système de logs"""
        status_lines = []
        
        # Test 1: Existence du fichier
        if os.path.exists(self.log_file_path):
            file_size = os.path.getsize(self.log_file_path)
            status_lines.append(f"[TEST] ✓ Fichier de log trouvé: {self.log_file_path}")
            status_lines.append(f"[TEST] ✓ Taille du fichier: {file_size} bytes")
            status_lines.append(f"[TEST] ✓ Position de lecture actuelle: {self.log_position}")
        else:
            status_lines.append(f"[TEST] ✗ Fichier de log non trouvé: {self.log_file_path}")
        
        # Test 2: État de la surveillance
        status_lines.append(f"[TEST] Surveillance active: {'✓ OUI' if self.check_logs_running else '✗ NON'}")
        
        # Test 3: Tentative de lecture
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    line_count = content.count('\n')
                    status_lines.append(f"[TEST] ✓ Lecture réussie - {line_count} lignes")
                    
                    # Afficher les dernières lignes
                    last_lines = content.strip().split('\n')[-3:] if content.strip() else []
                    if last_lines:
                        status_lines.append("[TEST] Dernières entrées:")
                        for line in last_lines:
                            if line.strip():
                                status_lines.append(f"[TEST]   > {line[:80]}...")
            else:
                status_lines.append("[TEST] ✗ Impossible de lire le fichier")
                
        except Exception as e:
            status_lines.append(f"[TEST] ✗ Erreur de lecture: {str(e)}")
        
        # Test 4: Écriture d'un message de test
        try:
            import logging
            test_logger = logging.getLogger("ui_test")
            test_logger.info("Message de test depuis l'interface")
            status_lines.append("[TEST] ✓ Message de test écrit dans les logs")
        except Exception as e:
            status_lines.append(f"[TEST] ✗ Erreur d'écriture: {str(e)}")
        
        # Afficher tous les résultats
        test_content = '\n'.join(status_lines) + '\n'
        self.display_log_content(test_content)
    
    def show_help(self):
        """Affiche l'aide"""
        help_text = """
Générateur de Tests Unitaires avec Ollama

UTILISATION:
1. Sélectionnez le répertoire contenant votre code Python
2. Configurez les paramètres selon vos besoins
3. Cliquez sur "Générer les tests"

PARAMÈTRES PRINCIPAUX:
• Répertoire source: Dossier contenant les fichiers Python à analyser
• Répertoire de sortie: Où sauvegarder les tests générés
• Modèle: Le modèle Ollama à utiliser (ex: llama3:8b, codellama)
• Hôte: Adresse du serveur Ollama

OPTIONS:
• Mode verbose: Affiche plus de détails dans les logs
• Mode simulation: Analyse sans générer les fichiers
• Traitement minimal: Mode préservant la syntaxe
• Créer environnement virtuel: Génère les scripts d'installation

EXCLUSIONS:
Vous pouvez exclure certains dossiers ou fichiers de l'analyse.
Séparez les éléments par des virgules.

LOGS:
La zone de logs affiche en temps réel les informations
de progression et les erreurs éventuelles.
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Aide")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        close_btn = ttk.Button(help_window, text="Fermer", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def on_source_dir_changed(self, *args):
        """Appelé automatiquement quand le répertoire source change"""
        source_path = self.source_dir.get().strip()
        if source_path and os.path.exists(source_path):
            # Définir automatiquement le répertoire de sortie
            default_output = os.path.join(source_path, "tests")
            self.output_dir.set(default_output)
    
    def get_output_dir(self):
        """Retourne le répertoire de sortie à utiliser"""
        output = self.output_dir.get().strip()
        if not output:
            # Si aucun répertoire de sortie n'est défini, utiliser source_dir/tests
            source_path = self.source_dir.get().strip()
            if source_path:
                return os.path.join(source_path, "tests")
            else:
                return "./tests"  # Fallback par défaut
        return output


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    app = TestGeneratorUI(root)
    
    # Configuration pour fermer proprement
    def on_closing():
        app.check_logs_running = False
        if hasattr(app, 'log_status_label'):
            app.log_status_label.config(text="📄 Logs: ⏹ Arrêté", foreground="gray")
        if hasattr(app, 'process') and app.process:
            app.process.terminate()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Centrage de la fenêtre
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
