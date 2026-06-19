#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZEPHYR - Minutiae Extractor
Extração de características de Nível 1, 2 e 3 usando CNN.
Versão: 3.0.0
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple
import cv2
import asyncio

logger = logging.getLogger(__name__)


class MinutiaeExtractor:
    """
    Extrator de minúcias e características de impressões digitais.
    Nível 1: Fluxo global (Arch, Loop, Whorl)
    Nível 2: Minúcias (bifurcações, terminações, ilhas, pontos)
    Nível 3: Poros e arestas
    """

    def __init__(self, models_config: Dict):
        self.models_config = models_config
        self.cnn_model = None
        self.pore_model = None
        self._loaded = False

    async def load_models(self) -> bool:
        """
        Carrega os modelos CNN para extração.
        """
        try:
            logger.info("   📦 Carregando modelos de extração (CNN)...")

            # Em produção: self.cnn_model = torch.load(...)
            # self.pore_model = torch.load(...)

            self._loaded = True
            logger.info("   ✅ Modelos de extração carregados.")
            return True
        except Exception as e:
            logger.error(f"   ❌ Erro ao carregar modelos de extração: {e}")
            return False

    async def extract(
        self,
        image: np.ndarray,
        extract_pores: bool = True,
        extract_flow: bool = True
    ) -> Tuple[List[Dict], np.ndarray]:
        """
        Extrai minúcias e vetor de embedding.

        Args:
            image: Imagem processada (grayscale)
            extract_pores: Extrair poros (Nível 3)
            extract_flow: Extrair fluxo global (Nível 1)

        Returns:
            Tuplo (lista de minúcias, vetor de embedding)
        """
        logger.info("   🔬 Extraindo características...")

        # 1. Deteção de fluxo global (Nível 1)
        flow_data = self._extract_flow(image) if extract_flow else {}

        # 2. Extração de minúcias (Nível 2) - usando método baseado em morfologia
        minutiae = self._extract_minutiae(image)

        # 3. Extração de poros (Nível 3)
        pore_data = self._extract_pores(image) if extract_pores else {}

        # Combinar informações
        combined_minutiae = []
        for m in minutiae:
            m['level1'] = flow_data
            m['level3'] = pore_data.get(m.get('id'), {})
            combined_minutiae.append(m)

        # 4. Gerar embedding (vetor de características)
        embedding = self._generate_embedding(image, combined_minutiae)

        logger.info(f"   ✅ Extração concluída. Minúcias: {len(combined_minutiae)}")
        return combined_minutiae, embedding

    def _extract_flow(self, image: np.ndarray) -> Dict:
        """
        Determina o fluxo global das cristas (Arch, Loop, Whorl).
        """
        # Usar gradientes para orientação
        gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)

        magnitude = np.sqrt(gx**2 + gy**2)
        angle = np.arctan2(gy, gx) * 180 / np.pi

        # Estatísticas de orientação
        mean_angle = np.mean(angle)
        std_angle = np.std(angle)

        if std_angle < 30:
            pattern = 'Arch'
            henry_index = 1
        elif 30 <= std_angle < 60:
            pattern = 'Loop'
            henry_index = 2
        else:
            pattern = 'Whorl'
            henry_index = 3

        return {
            'pattern': pattern,
            'henry_index': henry_index,
            'mean_angle': float(mean_angle),
            'std_angle': float(std_angle),
            'confidence': 0.99
        }

    def _extract_minutiae(self, image: np.ndarray) -> List[Dict]:
        """
        Extrai minúcias usando esqueletização e análise de vizinhança.
        """
        # Pré-processamento: binarização e esqueletização
        _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
        skeleton = cv2.ximgproc.thinning(binary)

        # Encontrar pontos de minúcia
        minutiae = []
        h, w = skeleton.shape

        # Usar convolução para detetar terminações e bifurcações
        kernel = np.ones((3, 3), np.uint8)
        # Remover bordas para evitar falsos
        for y in range(1, h-1):
            for x in range(1, w-1):
                if skeleton[y, x] == 255:
                    # Contar vizinhos na região 3x3
                    patch = skeleton[y-1:y+2, x-1:x+2] // 255
                    neighbors = np.sum(patch) - 1  # menos o centro

                    if neighbors == 1:
                        minutiae.append({
                            'id': len(minutiae) + 1,
                            'x': float(x),
                            'y': float(y),
                            'angle': 0.0,  # calcular em produção
                            'type': 'termination',
                            'confidence': 0.99
                        })
                    elif neighbors == 3:
                        minutiae.append({
                            'id': len(minutiae) + 1,
                            'x': float(x),
                            'y': float(y),
                            'angle': 0.0,
                            'type': 'bifurcation',
                            'confidence': 0.98
                        })
                    elif neighbors == 0:
                        minutiae.append({
                            'id': len(minutiae) + 1,
                            'x': float(x),
                            'y': float(y),
                            'angle': 0.0,
                            'type': 'island',
                            'confidence': 0.95
                        })

        # Limitar número máximo de minúcias (para performance)
        if len(minutiae) > 60:
            # Manter as com maior confiança
            minutiae = sorted(minutiae, key=lambda m: m['confidence'], reverse=True)[:60]

        # Atualizar IDs
        for i, m in enumerate(minutiae):
            m['id'] = i + 1

        return minutiae

    def _extract_pores(self, image: np.ndarray) -> Dict:
        """
        Extrai poros (Nível 3) - simulação.
        Em produção: usar modelo treinado para deteção de poros.
        """
        # Simulação: detetar pequenos pontos escuros
        _, binary = cv2.threshold(image, 120, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        pores = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 1 < area < 15:  # poros têm áreas pequenas
                pores.append({
                    'x': float(cnt[0][0][0]),
                    'y': float(cnt[0][0][1])
                })

        return {
            'total': len(pores),
            'pores': pores[:100],  # limitar para performance
            'confidence': 0.95
        }

    def _generate_embedding(self, image: np.ndarray, minutiae: List[Dict]) -> np.ndarray:
        """
        Gera um vetor de embedding de alta dimensão (1024-d) a partir da imagem e minúcias.
        """
        # Simulação: em produção, usar CNN para extrair embedding
        # Aqui usamos uma combinação de características manuais

        # 1. Características globais da imagem
        mean_val = np.mean(image)
        std_val = np.std(image)
        hist = np.histogram(image, bins=32)[0] / image.size

        # 2. Características das minúcias
        if minutiae:
            types = [m['type'] for m in minutiae]
            type_counts = {
                'bifurcation': types.count('bifurcation'),
                'termination': types.count('termination'),
                'island': types.count('island'),
                'dot': types.count('dot')
            }
        else:
            type_counts = {'bifurcation': 0, 'termination': 0, 'island': 0, 'dot': 0}

        # 3. Características de densidade
        density = len(minutiae) / (image.shape[0] * image.shape[1]) * 10000

        # 4. Características de orientação (simplificado)
        gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
        orient_mean = np.mean(np.arctan2(gy, gx))

        # Combinar tudo num vetor 1024-d (preencher com zeros)
        embedding = np.zeros(1024, dtype=np.float32)
        embedding[0] = mean_val / 255.0
        embedding[1] = std_val / 255.0
        embedding[2:34] = hist
        embedding[34] = type_counts['bifurcation'] / 20.0
        embedding[35] = type_counts['termination'] / 20.0
        embedding[36] = type_counts['island'] / 10.0
        embedding[37] = type_counts['dot'] / 10.0
        embedding[38] = density / 10.0
        embedding[39] = orient_mean / np.pi

        # Normalizar
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        return embedding