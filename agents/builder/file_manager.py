"""
File Manager module for Builder Agent.

Handles safe read/write operations, path validation, and backup creation.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class FileManager:
    """
    Manages safe file operations with backup and validation.
    
    TODO: Add file locking for concurrent access
    TODO: Implement file versioning system
    TODO: Add encryption for sensitive files
    TODO: Implement file change tracking
    """
    
    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize the file manager.
        
        Args:
            backup_dir: Directory for backups. Defaults to ./backups/
        """
        self.backup_dir = Path(backup_dir) if backup_dir else Path("./backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def read_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Safely read a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Tuple of (success: bool, content: str or None, error: str or None)
        """
        try:
            path = Path(file_path)
            
            # Validate path
            if not path.exists():
                return False, None, f"File does not exist: {file_path}"
            
            if not path.is_file():
                return False, None, f"Path is not a file: {file_path}"
            
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return True, content, None
            
        except PermissionError as e:
            return False, None, f"Permission denied: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"
    
    def write_file(self, file_path: str, content: str, create_backup: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Safely write a file with optional backup.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            create_backup: Whether to create a backup if file exists
            
        Returns:
            Tuple of (success: bool, backup_path: str or None, error: str or None)
        """
        try:
            path = Path(file_path)
            
            # Validate path
            validation_result = self.validate_path(file_path, must_exist=False)
            if not validation_result[0]:
                return False, None, validation_result[1]
            
            # Create backup if file exists
            backup_path = None
            if path.exists() and create_backup:
                backup_result = self.backup_file(file_path)
                if not backup_result[0]:
                    return False, None, f"Failed to create backup: {backup_result[1]}"
                backup_path = backup_result[1]
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, backup_path, None
            
        except PermissionError as e:
            return False, None, f"Permission denied: {str(e)}"
        except Exception as e:
            return False, None, f"Error writing file: {str(e)}"
    
    def backup_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a backup of an existing file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Tuple of (success: bool, backup_path: str or None, error: str or None)
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, None, f"File does not exist: {file_path}"
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{path.stem}_{timestamp}{path.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            # Copy file to backup location
            shutil.copy2(path, backup_path)
            
            return True, str(backup_path), None
            
        except Exception as e:
            return False, None, f"Error creating backup: {str(e)}"
    
    def validate_path(self, file_path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate a file path.
        
        Args:
            file_path: Path to validate
            must_exist: Whether the file must exist
            
        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        try:
            path = Path(file_path)
            
            # Check for path traversal attempts
            resolved = path.resolve()
            if '..' in str(path):
                return False, "Path traversal detected"
            
            # Check if must exist
            if must_exist and not path.exists():
                return False, f"File does not exist: {file_path}"
            
            # Check if parent directory is writable (for new files)
            if not must_exist:
                parent = path.parent
                if parent.exists() and not os.access(parent, os.W_OK):
                    return False, f"Parent directory is not writable: {parent}"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file info or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "path": str(path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
        except Exception:
            return None

