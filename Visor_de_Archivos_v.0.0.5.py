import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog, Menu
import json
import os
from PIL import Image, ImageTk

class VisorArchivos:
    def __init__(self, root):
        self.root = root
        self.root.title("Visor de Estructura de Archivos")
        
        # Cargar iconos
        self.iconos = {}
        self.cargar_iconos()
        
        # Variables para el seguimiento de nodos y líneas
        self.nodos = []
        self.nodo_seleccionado = None
        self.lineas = []
        
        # Canvas principal
        self.canvas = tk.Canvas(root, width=800, height=600, bg='white', scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(expand=True, fill='both')        
        # Scrollbars
        self.vscroll = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.hscroll = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vscroll.set, xscrollcommand=self.hscroll.set)
        
        # Configurar scroll
        self.vscroll.pack(side="right", fill="y")
        self.hscroll.pack(side="bottom", fill="x")
        
        # Barra de herramientas
        self.frame_botones = ttk.Frame(root)
        self.frame_botones.pack(pady=5)
        
        ttk.Button(self.frame_botones, text="Importar JSON", 
                  command=self.cargar_estructura).pack(side='left', padx=5)
        ttk.Button(self.frame_botones, text="Exportar JSON", 
                  command=self.guardar_estructura).pack(side='left', padx=5)
        ttk.Button(self.frame_botones, text="Generar Archivos", 
                  command=self.generar_archivos).pack(side='left', padx=5)

        # Crear menús contextuales
        self.crear_menus_contextuales()
        
        # Eventos del ratón
        self.canvas.bind('<Button-1>', self.click_izquierdo)
        self.canvas.bind('<B1-Motion>', self.mover_nodo)
        self.canvas.bind('<ButtonRelease-1>', self.finalizar_movimiento)
        self.canvas.bind('<Button-3>', self.mostrar_menu_contextual)

    def cargar_iconos(self):
        try:
            iconos_paths = {
                "carpeta": "folder.png",
                "script": "script.png",
                "imagen": "image.png"
            }
            
            for tipo, path in iconos_paths.items():
                if os.path.exists(path):
                    imagen = Image.open(path)
                    imagen = imagen.resize((24, 24))
                    self.iconos[tipo] = ImageTk.PhotoImage(imagen)
                else:
                    print(f"No se encontró el icono {path}")
            
            if os.path.exists("file.png"):
                imagen = Image.open("file.png")
                imagen = imagen.resize((24, 24))
                self.iconos["archivo"] = ImageTk.PhotoImage(imagen)
            
        except Exception as e:
            print(f"Error al cargar iconos: {e}")

    def crear_menus_contextuales(self):
        self.menu_canvas = Menu(self.root, tearoff=0)
        self.menu_canvas.add_command(label="Crear Nodo Matriz", 
                                   command=self.crear_nodo_matriz)
        
        self.menu_nodo = Menu(self.root, tearoff=0)
        self.menu_nodo.add_command(label="Editar", command=self.editar_nodo_actual)
        self.menu_nodo.add_command(label="Crear Nodo Hijo", 
                                 command=self.crear_nodo_hijo)
        self.menu_nodo.add_separator()
        self.menu_nodo.add_command(label="Eliminar (y descendientes)", 
                                 command=self.eliminar_nodo_y_descendientes)

# SUSTITUIR DESDE AQUÍ HASTA encontrar_nodo, click_izquierdo, mover_nodo Y OTROS MANEJADORES DE EVENTOS:

    def encontrar_nodo(self, x, y):
        # Convertir coordenadas del evento a coordenadas del canvas
        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        
        for nodo in self.nodos:
            coords = self.canvas.bbox(nodo["rect"])
            if coords and coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                return nodo
        return None

    def click_izquierdo(self, event):
        self.nodo_seleccionado = self.encontrar_nodo(event.x, event.y)

    def mover_nodo(self, event):
        if self.nodo_seleccionado:
            # Convertir coordenadas del evento a coordenadas del canvas
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            coords = self.canvas.bbox(self.nodo_seleccionado["rect"])
            dx = x - (coords[0] + 150)  # Ajustado para el nuevo ancho del nodo
            dy = y - (coords[1] + 20)
            
            self.canvas.move(self.nodo_seleccionado["rect"], dx, dy)
            self.canvas.move(self.nodo_seleccionado["texto"], dx, dy)
            if self.nodo_seleccionado.get("icono"):
                self.canvas.move(self.nodo_seleccionado["icono"], dx, dy)
            
            self.actualizar_conexiones_recursivas(self.nodo_seleccionado)

    def actualizar_conexiones_recursivas(self, nodo):
        for conexion in self.lineas:
            if conexion["padre"] == nodo or conexion["hijo"] == nodo:
                self.actualizar_conexion(conexion)
        
        for hijo in nodo["hijos"]:
            self.actualizar_conexiones_recursivas(hijo)

    def finalizar_movimiento(self, event):
        self.nodo_seleccionado = None

    def mostrar_menu_contextual(self, event):
        nodo_clickeado = self.encontrar_nodo(event.x, event.y)
        
        if nodo_clickeado:
            self.nodo_seleccionado = nodo_clickeado
            self.menu_nodo.post(event.x_root, event.y_root)
        else:
            self.menu_canvas.post(event.x_root, event.y_root)

    def crear_nodo_matriz(self):
        dialog = NodoConfigDialog(self.root, "Configurar Nodo Matriz")
        if dialog.result:
            nombre, tipo, datos_extra = dialog.result
            x, y = 100, 100
            self.crear_nodo(nombre, tipo, x, y, datos_extra)

    def crear_nodo_hijo(self):
        if not self.nodo_seleccionado:
            return
            
        dialog = NodoConfigDialog(self.root, "Configurar Nodo Hijo")
        if dialog.result:
            nombre, tipo, datos_extra = dialog.result
            coords = self.canvas.bbox(self.nodo_seleccionado["rect"])
            x = coords[0] + 200
            y = coords[1] + 80
            
            nuevo_nodo = self.crear_nodo(nombre, tipo, x, y, datos_extra)
            self.crear_conexion(self.nodo_seleccionado, nuevo_nodo)

    def crear_nodo(self, nombre, tipo, x, y, datos_extra=None):
        colores = {
            "carpeta": "#FFE5B4",
            "imagen": "#E0FFE0",
            "script": "#E0E0FF",
            "archivo": "#FFFFFF"
        }
        color = colores.get(tipo, "#FFFFFF")
        
        ancho_nodo = 300
        alto_nodo = 40
        rect = self.canvas.create_rectangle(x, y, x + ancho_nodo, y + alto_nodo, fill=color)
        
        icono_id = None
        if tipo in self.iconos:
            icono_id = self.canvas.create_image(x + 30, y + (alto_nodo/2), image=self.iconos[tipo])
        
        texto = self.canvas.create_text(x + 160, y + (alto_nodo/2), text=nombre)
        
        nodo = {
            "rect": rect,
            "icono": icono_id,
            "texto": texto,
            "tipo": tipo,
            "nombre": nombre,
            "conexiones": [],
            "hijos": [],
            "datos_extra": datos_extra or {}
        }
        
        self.nodos.append(nodo)
        return nodo

    def crear_conexion(self, padre, hijo):
        coords_padre = self.canvas.bbox(padre["rect"])
        coords_hijo = self.canvas.bbox(hijo["rect"])
        
        x1 = (coords_padre[0] + coords_padre[2]) / 2
        y1 = coords_padre[3]
        
        x2 = coords_hijo[0]
        y2 = (coords_hijo[1] + coords_hijo[3]) / 2
        
        linea_vertical = self.canvas.create_line(x1, y1, x1, y2, width=2)
        linea_horizontal = self.canvas.create_line(x1, y2, x2, y2, width=2)
        
        conexion = {
            "linea_vertical": linea_vertical,
            "linea_horizontal": linea_horizontal,
            "padre": padre,
            "hijo": hijo,
            "nivel_y": y2
        }
        self.lineas.append(conexion)
        
        padre["hijos"].append(hijo)
        padre["conexiones"].extend([linea_vertical, linea_horizontal])
        hijo["conexiones"].extend([linea_vertical, linea_horizontal])

    def actualizar_conexion(self, conexion):
        coords_padre = self.canvas.bbox(conexion["padre"]["rect"])
        coords_hijo = self.canvas.bbox(conexion["hijo"]["rect"])
        
        x_padre = (coords_padre[0] + coords_padre[2]) / 2
        y_padre = coords_padre[3]
        
        x_hijo = coords_hijo[0]
        y_hijo = (coords_hijo[1] + coords_hijo[3]) / 2
        
        self.canvas.coords(conexion["linea_vertical"], 
                         x_padre, y_padre, 
                         x_padre, y_hijo)
        self.canvas.coords(conexion["linea_horizontal"], 
                         x_padre, y_hijo, 
                         x_hijo, y_hijo)

    def editar_nodo_actual(self):
        if not self.nodo_seleccionado:
            return
            
        dialog = NodoConfigDialog(
            self.root, 
            "Editar Nodo",
            inicial_nombre=self.nodo_seleccionado["nombre"],
            inicial_tipo=self.nodo_seleccionado["tipo"],
            inicial_datos=self.nodo_seleccionado["datos_extra"]
        )
        
        if dialog.result:
            nombre, tipo, datos_extra = dialog.result
            self.nodo_seleccionado["nombre"] = nombre
            self.nodo_seleccionado["tipo"] = tipo
            self.nodo_seleccionado["datos_extra"] = datos_extra
            
            self.canvas.itemconfig(self.nodo_seleccionado["texto"], text=nombre)
            
            if self.nodo_seleccionado["icono"]:
                self.canvas.delete(self.nodo_seleccionado["icono"])
            if tipo in self.iconos:
                coords = self.canvas.bbox(self.nodo_seleccionado["rect"])
                self.nodo_seleccionado["icono"] = self.canvas.create_image(
                    coords[0] + 30, (coords[1] + coords[3])/2, 
                    image=self.iconos[tipo]
                )
            
            colores = {
                "carpeta": "#FFE5B4",
                "imagen": "#E0FFE0",
                "script": "#E0E0FF",
                "archivo": "#FFFFFF"
            }
            self.canvas.itemconfig(
                self.nodo_seleccionado["rect"], 
                fill=colores.get(tipo, "#FFFFFF")
            )

    def eliminar_nodo_y_descendientes(self):
        if not self.nodo_seleccionado:
            return
            
        self.eliminar_nodo_recursivo(self.nodo_seleccionado)
        self.nodo_seleccionado = None

    def eliminar_nodo_recursivo(self, nodo):
        for hijo in nodo["hijos"][:]:
            self.eliminar_nodo_recursivo(hijo)
        
        for linea in nodo["conexiones"]:
            self.canvas.delete(linea)
        
        self.lineas = [l for l in self.lineas 
                      if l["linea_vertical"] not in nodo["conexiones"] and 
                         l["linea_horizontal"] not in nodo["conexiones"]]
        
        self.canvas.delete(nodo["rect"])
        self.canvas.delete(nodo["texto"])
        if nodo.get("icono"):
            self.canvas.delete(nodo["icono"])
        
        if nodo in self.nodos:
            self.nodos.remove(nodo)

    def guardar_estructura(self):
        try:
            datos = self.serializar_estructura()
            
            # Pre-procesar los datos para mantener el formato del código
            for nodo in datos["nodos"]:
                if nodo["tipo"] == "script" and "datos_extra" in nodo:
                    # Asegurarse de que el contenido del script mantenga su formato
                    contenido = nodo["datos_extra"].get("contenido", "")
                    if isinstance(contenido, str):
                        # Preservar la indentación y los saltos de línea
                        nodo["datos_extra"]["contenido"] = contenido.rstrip()
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Éxito", "Estructura guardada correctamente")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")

# SUSTITUIR DESDE AQUÍ HASTA EL FINAL DEL ARCHIVO:

    def serializar_estructura(self):
        datos = {
            "nodos": [],
            "conexiones": []
        }
        
        for nodo in self.nodos:
            coords = self.canvas.coords(nodo["rect"])
            nodo_data = {
                "tipo": nodo["tipo"],
                "nombre": nodo["nombre"],
                "x": coords[0],
                "y": coords[1],
                "datos_extra": {}
            }
            
            # Manejar datos extra específicamente para mantener el formato
            if nodo["tipo"] == "script":
                nodo_data["datos_extra"] = {
                    "extension": nodo["datos_extra"].get("extension", ".py"),
                    "contenido": nodo["datos_extra"].get("contenido", "").rstrip()
                }
            elif nodo["tipo"] == "imagen":
                nodo_data["datos_extra"] = {
                    "ancho": nodo["datos_extra"].get("ancho", 100),
                    "alto": nodo["datos_extra"].get("alto", 100),
                    "ruta_original": nodo["datos_extra"].get("ruta_original")
                }
            else:
                nodo_data["datos_extra"] = nodo["datos_extra"]
            
            datos["nodos"].append(nodo_data)
        
        for conexion in self.lineas:
            origen_idx = self.nodos.index(conexion["padre"])
            destino_idx = self.nodos.index(conexion["hijo"])
            datos["conexiones"].append({
                "padre": origen_idx,
                "hijo": destino_idx
            })
        
        return datos

    def cargar_estructura(self):
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filename:
                return
            
            # Limpiar canvas actual
            self.canvas.delete("all")
            self.nodos = []
            self.lineas = []
            
            # Cargar datos preservando formato
            with open(filename, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # Recrear nodos manteniendo el formato del contenido
            for nodo_data in datos["nodos"]:
                # Pre-procesar datos extra para scripts
                if nodo_data["tipo"] == "script" and "datos_extra" in nodo_data:
                    contenido = nodo_data["datos_extra"].get("contenido", "")
                    if isinstance(contenido, str):
                        nodo_data["datos_extra"]["contenido"] = contenido
                
                self.crear_nodo(
                    nodo_data["nombre"],
                    nodo_data["tipo"],
                    nodo_data["x"],
                    nodo_data["y"],
                    nodo_data.get("datos_extra", {})
                )
            
            # Recrear conexiones
            for conn in datos["conexiones"]:
                padre = self.nodos[conn["padre"]]
                hijo = self.nodos[conn["hijo"]]
                self.crear_conexion(padre, hijo)
            
            messagebox.showinfo("Éxito", "Estructura cargada correctamente")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {str(e)}")

    def generar_archivos(self):
        if not self.nodos:
            messagebox.showwarning("Aviso", "No hay estructura para generar")
            return
            
        # Pedir directorio base
        dir_base = filedialog.askdirectory(title="Seleccionar directorio base")
        if not dir_base:
            return
            
        try:
            # Encontrar nodos raíz
            nodos_raiz = []
            for nodo in self.nodos:
                es_hijo = False
                for conexion in self.lineas:
                    if conexion["hijo"] == nodo:
                        es_hijo = True
                        break
                if not es_hijo:
                    nodos_raiz.append(nodo)
            
            if not nodos_raiz:
                messagebox.showwarning("Aviso", "No se encontraron nodos raíz")
                return
            
            # Generar estructura para cada nodo raíz
            for nodo in nodos_raiz:
                self.generar_estructura_recursiva(nodo, dir_base)
            
            messagebox.showinfo("Éxito", "Estructura de archivos generada correctamente")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar estructura: {str(e)}")

    def generar_estructura_recursiva(self, nodo, path_actual):
        try:
            nombre_seguro = "".join(c for c in nodo["nombre"] if c.isalnum() or c in (' ', '-', '_', '.'))
            path_completo = os.path.join(path_actual, nombre_seguro)
            
            if nodo["tipo"] == "carpeta":
                os.makedirs(path_completo, exist_ok=True)
                for hijo in nodo["hijos"]:
                    self.generar_estructura_recursiva(hijo, path_completo)
            else:
                try:
                    if nodo["tipo"] == "imagen":
                        datos_extra = nodo.get("datos_extra", {})
                        ruta_original = datos_extra.get("ruta_original")
                        if ruta_original and os.path.exists(ruta_original):
                            # Si tenemos la ruta original y existe, copiamos el archivo
                            import shutil
                            shutil.copy2(ruta_original, path_completo)
                        else:
                            # Si no tenemos la ruta original, creamos una imagen en blanco
                            ancho = int(datos_extra.get("ancho", 100))
                            alto = int(datos_extra.get("alto", 100))
                            Image.new('RGB', (ancho, alto), 'white').save(path_completo)
                    
                    elif nodo["tipo"] == "script":
                        datos_extra = nodo.get("datos_extra", {})
                        contenido = datos_extra.get("contenido", "")
                        if not isinstance(contenido, str):
                            contenido = str(contenido)
                        with open(path_completo, 'w', encoding='utf-8') as f:
                            f.write(contenido)
                    
                    else:
                        open(path_completo, 'a').close()
                
                except Exception as e:
                    messagebox.showerror("Error", f"Error al crear {nombre_seguro}: {str(e)}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar estructura: {str(e)}")


class NodoConfigDialog:
    def __init__(self, parent, titulo, inicial_nombre="", inicial_tipo="carpeta", inicial_datos=None):
        self.result = None
        self.imagen_data = None
        
        # Crear diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Aumentar el tamaño inicial del diálogo
        self.dialog.geometry('600x700')
        
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión del grid
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Campos básicos
        ttk.Label(main_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.nombre = ttk.Entry(main_frame, width=50)
        self.nombre.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        # Remover la extensión del nombre inicial si es un script
        if inicial_tipo == "script" and inicial_nombre:
            inicial_nombre = os.path.splitext(inicial_nombre)[0]
        self.nombre.insert(0, inicial_nombre)
        
        ttk.Label(main_frame, text="Tipo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tipo = ttk.Combobox(main_frame, 
                                values=["carpeta", "imagen", "script"],  # Eliminado "archivo"
                                state="readonly", width=47)
        self.tipo.grid(row=1, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)
        self.tipo.set(inicial_tipo)
        
        # Frame para campos adicionales
        self.frame_extra = ttk.Frame(main_frame)
        self.frame_extra.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E+tk.N+tk.S, pady=10)
        self.frame_extra.grid_columnconfigure(1, weight=1)
        
        # Configurar campos según tipo
        self.campos_extra = {}
        self.tipo.bind('<<ComboboxSelected>>', self.actualizar_campos_extra)
        
        # Botones
        frame_botones = ttk.Frame(main_frame)
        frame_botones.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(frame_botones, text="Aceptar", 
                  command=self.finalizar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Inicializar campos extra
        self.tipo.set(inicial_tipo)
        self.actualizar_campos_extra(None)
        if inicial_datos:
            self.cargar_datos_iniciales(inicial_datos)
        
        # Hacer foco en el campo nombre
        self.nombre.focus_set()
        
        # Esperar hasta que se cierre el diálogo
        self.dialog.wait_window()

    def actualizar_campos_extra(self, event):
        # Limpiar frame actual
        for widget in self.frame_extra.winfo_children():
            widget.destroy()
        self.campos_extra.clear()
        
        tipo_actual = self.tipo.get()
        
        if tipo_actual == "imagen":
            ttk.Label(self.frame_extra, text="Dimensiones:").grid(row=0, column=0, sticky=tk.W, padx=5)
            
            frame_dim = ttk.Frame(self.frame_extra)
            frame_dim.grid(row=0, column=1, sticky=tk.W, pady=5)
            
            self.campos_extra["ancho"] = ttk.Entry(frame_dim, width=8)
            self.campos_extra["ancho"].pack(side=tk.LEFT, padx=2)
            ttk.Label(frame_dim, text="x").pack(side=tk.LEFT, padx=2)
            self.campos_extra["alto"] = ttk.Entry(frame_dim, width=8)
            self.campos_extra["alto"].pack(side=tk.LEFT, padx=2)
            
            ttk.Button(self.frame_extra, text="Seleccionar Imagen",
                      command=self.seleccionar_imagen).grid(row=1, column=0, 
                                                          columnspan=2, pady=10)
            
        elif tipo_actual == "script":
            ttk.Label(self.frame_extra, text="Extensión:").grid(row=0, column=0, sticky=tk.W, padx=5)
            self.campos_extra["extension"] = ttk.Combobox(
                self.frame_extra,
                values=[".py", ".js", ".sh", ".sql", ".html", ".css", ".txt", ".bat"],  # Añadidas nuevas extensiones
                state="readonly",
                width=15
            )
            self.campos_extra["extension"].grid(row=0, column=1, sticky=tk.W, pady=5)
            self.campos_extra["extension"].set(".py")
            
            ttk.Label(self.frame_extra, text="Contenido:").grid(row=1, column=0, 
                                                              sticky=tk.W, padx=5, pady=5)
            
            self.campos_extra["contenido"] = tk.Text(self.frame_extra, 
                                                   height=30, width=60, 
                                                   wrap=tk.NONE)
            self.campos_extra["contenido"].grid(row=2, column=0, columnspan=2, 
                                             sticky=tk.W+tk.E+tk.N+tk.S, padx=5)
            
            # Scrollbars para el texto
            scrollbar_v = ttk.Scrollbar(self.frame_extra, 
                                    orient="vertical", 
                                    command=self.campos_extra["contenido"].yview)
            scrollbar_v.grid(row=2, column=2, sticky=tk.N+tk.S)
            
            scrollbar_h = ttk.Scrollbar(self.frame_extra,
                                    orient="horizontal",
                                    command=self.campos_extra["contenido"].xview)
            scrollbar_h.grid(row=3, column=0, columnspan=2, sticky=tk.E+tk.W)
            
            self.campos_extra["contenido"]["yscrollcommand"] = scrollbar_v.set
            self.campos_extra["contenido"]["xscrollcommand"] = scrollbar_h.set

    def seleccionar_imagen(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )
        if filename:
            try:
                imagen = Image.open(filename)
                self.campos_extra["ancho"].delete(0, tk.END)
                self.campos_extra["ancho"].insert(0, str(imagen.width))
                self.campos_extra["alto"].delete(0, tk.END)
                self.campos_extra["alto"].insert(0, str(imagen.height))
                # Guardamos la ruta del archivo original
                self.imagen_path = filename
                # Actualizar el nombre con el nombre del archivo de imagen
                nombre_archivo = os.path.basename(filename)
                self.nombre.delete(0, tk.END)
                self.nombre.insert(0, nombre_archivo)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar la imagen: {str(e)}")

    def cargar_datos_iniciales(self, datos):
        tipo = self.tipo.get()
        if tipo == "imagen":
            self.imagen_data = datos.get("imagen_data")
            self.campos_extra["ancho"].insert(0, str(datos.get("ancho", "100")))
            self.campos_extra["alto"].insert(0, str(datos.get("alto", "100")))
        elif tipo == "script":
            self.campos_extra["extension"].set(datos.get("extension", ".py"))
            contenido = datos.get("contenido", "")
            if isinstance(contenido, str):
                self.campos_extra["contenido"].insert("1.0", contenido)

    def finalizar(self):
        nombre = self.nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre no puede estar vacío")
            return
        
        tipo = self.tipo.get()
        datos_extra = {}
        
        if tipo == "imagen":
            try:
                ancho = int(self.campos_extra["ancho"].get())
                alto = int(self.campos_extra["alto"].get())
                datos_extra = {
                    "ancho": ancho,
                    "alto": alto,
                    "ruta_original": getattr(self, 'imagen_path', None)
                }
            except ValueError:
                messagebox.showerror("Error", "Las dimensiones deben ser números enteros")
                return
                
        elif tipo == "script":
            contenido = self.campos_extra["contenido"].get("1.0", "end-1c")
            extension = self.campos_extra["extension"].get()
            datos_extra = {
                "extension": extension,
                "contenido": contenido
            }
            # Solo añadir la extensión si el nombre no la tiene ya
            if not nombre.endswith(extension):
                nombre = nombre + extension
        
        self.result = (nombre, tipo, datos_extra)
        self.dialog.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VisorArchivos(root)
    root.mainloop()
