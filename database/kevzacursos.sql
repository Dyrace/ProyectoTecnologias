-- 1. Crear la base de datos.
CREATE DATABASE kevzacursos;

-- 2. Seleccionar la base de datos para trabajar.
USE kevzacursos;

-- 3. Crear tabla de categorías (almacena las categorías de los cursos).
CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT
);

-- 4. Crear tabla de cursos (almacena información sobre los cursos ofrecidos).
CREATE TABLE cursos (
    id_curso INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    duracion INT, -- en horas
    id_categoria INT,
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
);

-- 5. Crear tabla de participantes (almacena los datos personales de los participantes).
CREATE TABLE participantes (
    id_participante INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    telefono VARCHAR(15),
    direccion VARCHAR(255),
    edad INT,
    genero VARCHAR(10),
    ocupacion VARCHAR(100),
    fecha_registro DATE
);

-- 6. Crear tabla de inscripciones (relaciona participantes con cursos).
CREATE TABLE inscripciones (
    id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_curso INT,
    id_participante INT,
    fecha DATE,
    FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
    FOREIGN KEY (id_participante) REFERENCES participantes(id_participante)
);

-- 7. Insertar categorías predeterminadas (estas son las categorías que estarán disponibles inicialmente).
INSERT INTO categorias (nombre, descripcion) VALUES
('TECNOLOGIAS COMPUTACIONALES II', 'Curso sobre herramientas y lenguajes avanzados para el desarrollo de software.'),
('TECNOLOGÍAS COMPUTACIONALES I', 'Introducción a las tecnologías fundamentales para programación y hardware.'),
('INGENIERÍA DE SOFTWARE II', 'Profundización en metodologías, modelos y pruebas en el desarrollo de software.'),
('SISTEMAS ANALÓGICOS', 'Estudio de sistemas electrónicos analógicos y su aplicación.'),
('ANÁLISIS Y DISEÑO DE REDES', 'Fundamentos de diseño, topología y protocolos de redes.'),
('GRAFICACIÓN COMPUTACIONAL', 'Diseño y creación de gráficos digitales y visualización en 2D/3D.'),
('COMPILADORES', 'Construcción de compiladores, análisis léxico y sintáctico.');

-- Mostrar todas las categorías.
SELECT * FROM categorias;

-- Mostrar todos los cursos.
SELECT * FROM cursos;

-- Mostrar todos los participantes.
SELECT * FROM participantes;

-- Mostrar todas las inscripciones.
SELECT * FROM inscripciones;

-- Ver inscripciones con nombres de curso y participante.
SELECT 
    i.id_inscripcion,
    p.nombre AS participante,
    c.nombre AS curso,
    i.fecha
FROM inscripciones i
JOIN participantes p ON i.id_participante = p.id_participante
JOIN cursos c ON i.id_curso = c.id_curso;

ALTER TABLE participantes
ADD COLUMN usuario VARCHAR(50) UNIQUE,
ADD COLUMN password VARCHAR(255);

SHOW PROCESSLIST;
KILL 36;

SET SQL_SAFE_UPDATES = 0;

UPDATE participantes
SET usuario = NULL
WHERE usuario LIKE '%None%';
