#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZEPHYR - Chain of Custody Hasher
Sistema de selagem digital e cadeia de custódia
"""

import hashlib
import json
import time
import secrets
from datetime import datetime
from typing import Dict, Any, Optional, List
import hmac


class ChainOfCustodyHasher:
    """Gerencia a cadeia de custódia com criptografia SHA-3"""
    
    def __init__(self, secret_key: Optional[bytes] = None):
        """Inicializa o hasher da cadeia de custódia"""
        self.secret_key = secret_key or secrets.token_bytes(32)
        self.algorithm = 'sha3_256'
        self.history: List[Dict[str, Any]] = []
        self.current_hash: Optional[str] = None
        
    def hash_data(self, data: Any) -> str:
        """Gera hash SHA-3 de qualquer dado"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, dict):
            data = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, bytes):
            pass
        else:
            data = str(data).encode('utf-8')
            
        return hashlib.sha3_256(data).hexdigest()
    
    def seal_image(self, image_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sela uma imagem com hash imutável"""
        timestamp = datetime.now().isoformat()
        
        # Hash da imagem
        image_hash = self.hash_data(image_data)
        
        # Hash dos metadados
        metadata_hash = self.hash_data(metadata)
        
        # Hash combinado
        combined = f"{image_hash}{metadata_hash}{timestamp}{self.secret_key.hex()}"
        seal_hash = self.hash_data(combined)
        
        # Registrar na cadeia
        record = {
            'timestamp': timestamp,
            'image_hash': image_hash,
            'metadata_hash': metadata_hash,
            'seal_hash': seal_hash,
            'previous_hash': self.current_hash,
            'operation': 'seal'
        }
        
        self.history.append(record)
        self.current_hash = seal_hash
        
        return {
            'seal_hash': seal_hash,
            'image_hash': image_hash,
            'metadata_hash': metadata_hash,
            'timestamp': timestamp,
            'chain_index': len(self.history) - 1
        }
    
    def verify_integrity(self, seal_data: Dict[str, Any], image_data: bytes) -> bool:
        """Verifica a integridade de uma imagem selada"""
        # Recalcular hashes
        current_image_hash = self.hash_data(image_data)
        
        if current_image_hash != seal_data['image_hash']:
            return False
        
        # Verificar o selo
        combined = f"{seal_data['image_hash']}{seal_data['metadata_hash']}{seal_data['timestamp']}{self.secret_key.hex()}"
        calculated_seal = self.hash_data(combined)
        
        return calculated_seal == seal_data['seal_hash']
    
    def add_operation(self, operation: str, details: Dict[str, Any]) -> str:
        """Adiciona uma operação à cadeia de custódia"""
        timestamp = datetime.now().isoformat()
        
        record = {
            'timestamp': timestamp,
            'operation': operation,
            'details': details,
            'previous_hash': self.current_hash,
            'hash': None  # Será calculado abaixo
        }
        
        # Calcular hash do registro
        record_str = json.dumps(record, sort_keys=True)
        record_hash = self.hash_data(record_str)
        record['hash'] = record_hash
        
        self.history.append(record)
        self.current_hash = record_hash
        
        return record_hash
    
    def generate_audit_report(self) -> str:
        """Gera relatório de auditoria da cadeia de custódia"""
        report = {
            'total_operations': len(self.history),
            'current_hash': self.current_hash,
            'integrity_status': 'verified',
            'history': self.history
        }
        
        # Verificar integridade da cadeia
        for i in range(1, len(self.history)):
            if self.history[i]['previous_hash'] != self.history[i-1]['hash']:
                report['integrity_status'] = 'compromised'
                report['first_breach'] = i
                break
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def export_chain(self) -> str:
        """Exporta a cadeia de custódia completa"""
        return json.dumps({
            'chain': self.history,
            'current_hash': self.current_hash,
            'final_timestamp': datetime.now().isoformat()
        }, indent=2, ensure_ascii=False)
