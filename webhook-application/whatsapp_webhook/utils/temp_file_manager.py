"""
Gestor de archivos temporales para evitar memory leaks en Cloud Run.
Optimización de performance para prevenir acumulación de archivos temporales.
"""

import tempfile
import os
import atexit
import logging
from pathlib import Path
from typing import Set

class TempFileManager:
    """Gestor de archivos temporales para evitar memory leaks"""
    
    def __init__(self):
        self.temp_files: Set[str] = set()
        # Registrar cleanup al cerrar la aplicación
        atexit.register(self.cleanup_all)
        self.logger = logging.getLogger(__name__)
    
    def create_temp_file(self, suffix=".tmp", delete=False):
        """Crear archivo temporal tracked para cleanup automático"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=delete)
        self.temp_files.add(temp_file.name)
        self.logger.debug(f"Created temp file: {temp_file.name}")
        return temp_file
    
    def create_temp_directory(self):
        """Crear directorio temporal tracked"""
        temp_dir = tempfile.mkdtemp()
        self.temp_files.add(temp_dir)
        self.logger.debug(f"Created temp directory: {temp_dir}")
        return temp_dir
    
    def cleanup_file(self, filepath: str):
        """Limpiar archivo o directorio específico"""
        try:
            if os.path.isfile(filepath):
                os.unlink(filepath)
                self.logger.debug(f"Cleaned up temp file: {filepath}")
            elif os.path.isdir(filepath):
                import shutil
                shutil.rmtree(filepath)
                self.logger.debug(f"Cleaned up temp directory: {filepath}")
            
            self.temp_files.discard(filepath)
            
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp file {filepath}: {e}")
    
    def cleanup_all(self):
        """Limpiar todos los archivos temporales"""
        self.logger.info(f"Cleaning up {len(self.temp_files)} temporary files/directories")
        
        for filepath in list(self.temp_files):
            self.cleanup_file(filepath)
        
        self.temp_files.clear()
    
    def get_temp_file_count(self) -> int:
        """Obtener número de archivos temporales actuales"""
        return len(self.temp_files)

# Instancia global para usar en toda la aplicación
temp_manager = TempFileManager()
