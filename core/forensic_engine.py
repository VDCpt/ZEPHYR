#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZEPHYR - Forensic Engine
Motor orquestrador que coordena todo o fluxo de processamento forense.
Versão: 3.0.0
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import asyncio

from .image_processor import ImageProcessor
from .minutiae_extractor import MinutiaeExtractor
from .matching_engine import MatchingEngine
from .xai_explainer import XAIExplainer

# Configuração de logging
logger = logging.getLogger(__name__)


class ForensicEngine:
    """
    Motor principal do ZEPHYR.
    Orquestra: Restauro -> Extração -> Comparação -> Explicação -> Relatório
    """

    def __init__(self, legal_mode: str = 'PT/PT', config: Optional[Dict] = None):
        """
        Inicializa o motor forense.

        Args:
            legal_mode: Modo legal ('PT/PT' ou 'EN/US')
            config: Configurações adicionais
        """
        self.legal_mode = legal_mode
        self.config = config or {}
        self.initialized = False

        # Sub-módulos (inicializados sob demanda)
        self.image_processor = None
        self.minutiae_extractor = None
        self.matching_engine = None
        self.xai_explainer = None

        # Estado do processamento
        self.current_case_id = None
        self.processing_steps = []
        self.results_cache = {}

        logger.info(f"ForensicEngine inicializado (Modo: {legal_mode})")

    async def initialize(self) -> bool:
        """
        Inicializa todos os submódulos (carregamento de modelos).
        """
        if self.initialized:
            return True

        try:
            logger.info("🔄 Inicializando submódulos do motor forense...")

            # 1. Processador de Imagem (GAN)
            self.image_processor = ImageProcessor(self.config.get('models', {}))
            await self.image_processor.load_models()

            # 2. Extrator de Minúcias (CNN)
            self.minutiae_extractor = MinutiaeExtractor(self.config.get('models', {}))
            await self.minutiae_extractor.load_models()

            # 3. Motor de Comparação (Siamesa + Bayes)
            self.matching_engine = MatchingEngine(self.config.get('models', {}))
            await self.matching_engine.load_models()

            # 4. IA Explicável (XAI)
            self.xai_explainer = XAIExplainer(self.config.get('models', {}))
            await self.xai_explainer.load_models()

            self.initialized = True
            logger.info("✅ Todos os submódulos do motor forense inicializados com sucesso.")
            return True

        except Exception as e:
            logger.error(f"❌ Falha na inicialização do motor forense: {e}")
            return False

    async def process_fingerprint(
        self,
        image_data: bytes,
        case_id: str,
        metadata: Optional[Dict] = None,
        subject_id: Optional[str] = None,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Processa uma impressão digital do início ao fim.

        Args:
            image_data: Dados da imagem (bytes)
            case_id: Identificador único do caso
            metadata: Metadados da imagem (superfície, método, etc.)
            subject_id: ID do indivíduo para comparação (opcional)
            generate_report: Gerar relatório automaticamente

        Returns:
            Dicionário com resultados completos do processamento
        """
        if not self.initialized:
            await self.initialize()

        self.current_case_id = case_id
        self.processing_steps = []
        results = {
            'case_id': case_id,
            'status': 'processing',
            'timestamp': datetime.now().isoformat(),
            'legal_mode': self.legal_mode
        }

        try:
            # STEP 1: PRÉ-PROCESSAMENTO E RESTAURO
            logger.info(f"🔍 [Caso {case_id}] Iniciando pré-processamento...")
            processed_image, restoration_metrics = await self.image_processor.restore(
                image_data,
                metadata=metadata
            )
            self.processing_steps.append({
                'step': 'restoration',
                'status': 'success',
                'metrics': restoration_metrics
            })
            results['restoration'] = restoration_metrics

            # STEP 2: EXTRAÇÃO DE MINÚCIAS E VETOR
            logger.info(f"🔍 [Caso {case_id}] Extraindo características...")
            minutiae_data, embedding_vector = await self.minutiae_extractor.extract(
                processed_image,
                extract_pores=True,
                extract_flow=True
            )
            self.processing_steps.append({
                'step': 'extraction',
                'status': 'success',
                'minutiae_count': len(minutiae_data)
            })
            results['minutiae'] = minutiae_data
            results['embedding'] = embedding_vector.tolist()  # para JSON

            # STEP 3: COMPARAÇÃO (se subject_id fornecido)
            if subject_id:
                logger.info(f"🔍 [Caso {case_id}] Comparando com sujeito {subject_id}...")
                match_result = await self.matching_engine.match(
                    embedding_vector,
                    subject_id,
                    minutiae_data=minutiae_data
                )
                self.processing_steps.append({
                    'step': 'matching',
                    'status': 'success',
                    'score': match_result.get('confidence_score', 0)
                })
                results['match'] = match_result
            else:
                # Modo de busca apenas (sem sujeito específico)
                results['match'] = {'status': 'pending_search'}

            # STEP 4: IA EXPLICÁVEL (XAI) - Gera heatmaps e justificação
            logger.info(f"🔍 [Caso {case_id}] Gerando explicação XAI...")
            explainability_data = await self.xai_explainer.explain(
                processed_image,
                minutiae_data,
                match_result=match_result if subject_id else None
            )
            self.processing_steps.append({
                'step': 'xai',
                'status': 'success'
            })
            results['xai'] = explainability_data

            # STEP 5: DETECÇÃO DE VITALIDADE (anti-spoofing)
            logger.info(f"🔍 [Caso {case_id}] Verificando vitalidade...")
            vitality_result = await self.image_processor.check_vitality(
                processed_image,
                image_data
            )
            results['vitality'] = vitality_result
            self.processing_steps.append({
                'step': 'vitality',
                'status': 'success',
                'is_live': vitality_result.get('is_live', False)
            })

            # STEP 6: SEPARAÇÃO DE SOBREPOSIÇÕES (se detetado)
            if vitality_result.get('overlap_detected', False):
                logger.info(f"🔍 [Caso {case_id}] Separando sobreposições...")
                separated = await self.image_processor.separate_overlaps(
                    processed_image
                )
                results['overlap_separation'] = separated

            # STEP 7: VALIDAÇÃO FINAL E ASSINATURA
            final_hash = hashlib.sha3_256(
                json.dumps(results, sort_keys=True).encode()
            ).hexdigest()
            results['final_hash'] = final_hash
            results['status'] = 'completed'

            # Cache dos resultados
            self.results_cache[case_id] = results

            logger.info(f"✅ [Caso {case_id}] Processamento concluído com sucesso!")
            return results

        except Exception as e:
            logger.error(f"❌ [Caso {case_id}] Falha no processamento: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            return results

    async def match_against_database(
        self,
        embedding_vector: Any,
        database_id: str = 'local',
        top_k: int = 10
    ) -> List[Dict]:
        """
        Compara um vetor de embedding contra uma base de dados (local ou remota).

        Args:
            embedding_vector: Vetor de características da impressão
            database_id: Identificador da base de dados
            top_k: Número de melhores resultados

        Returns:
            Lista de correspondências com scores
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"🔎 Consultando base de dados: {database_id}")
        results = await self.matching_engine.search_database(
            embedding_vector,
            database_id,
            top_k=top_k
        )

        return results

    def get_case_results(self, case_id: str) -> Optional[Dict]:
        """Obtém os resultados de um caso processado anteriormente."""
        return self.results_cache.get(case_id)

    def get_processing_summary(self) -> Dict:
        """Retorna um resumo do estado do motor."""
        return {
            'initialized': self.initialized,
            'legal_mode': self.legal_mode,
            'cases_processed': len(self.results_cache),
            'last_case': self.current_case_id,
            'processing_steps': self.processing_steps[-5:]  # últimos 5 passos
        }
