-- Create database if not exists
CREATE DATABASE IF NOT EXISTS culturallm;
USE culturallm;

-- Create cultural themes table and insert initial data
CREATE TABLE IF NOT EXISTS cultural_themes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Insert initial cultural themes
INSERT INTO cultural_themes (name, description) VALUES
('Cucina Italiana', 'Tradizioni culinarie, piatti tipici, ingredienti regionali'),
('Televisione e Cinema', 'Programmi TV, film, attori e registi italiani'),
('Gestualità', 'Gesti tipici italiani e loro significati'),
('Dialetti e Lingue Regionali', 'Espressioni dialettali e varianti linguistiche'),
('Tradizioni Popolari', 'Feste, sagre, tradizioni locali'),
('Geografia e Paesaggi', 'Luoghi caratteristici, monumenti, paesaggi'),
('Storia e Personaggi', 'Eventi storici e personaggi famosi italiani'),
('Musica e Arte', 'Cantanti, artisti, opere d''arte italiane'),
('Sport', 'Calcio, altri sport, squadre e atleti italiani'),
('Vita Quotidiana', 'Abitudini, modi di dire, comportamenti tipici');

-- Create indexes for better performance
CREATE INDEX idx_cultural_themes_name ON cultural_themes(name);
