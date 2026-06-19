#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZEPHYR - Zero Entropy Fingerprint Hybrid Engine for Resolution
GERAR_RELATORIO_PERICIAL.PY
Motor de Geração de Relatórios Forenses
Versão: 3.0.0
Data: 2026-06-19
"""

import os
import sys
import json
import hashlib
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import base64

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
VERSION = "3.0.0"
SYSTEM_NAME = "ZEPHYR - Zero Entropy Fingerprint Hybrid Engine"


@dataclass
class MinutiaData:
    """Dados de uma minúcia"""
    id: int
    x: float
    y: float
    angle: float
    type: str  # 'bifurcation', 'termination', 'island', 'dot'
    confidence: float
    matched: bool = False


@dataclass
class FingerprintMatch:
    """Resultado de correspondência"""
    case_id: str
    subject_id: str
    subject_name: str
    confidence_score: float
    match_type: str  # 'positive', 'negative', 'inconclusive'
    minutiae_matched: int
    total_minutiae: int
    pores_matched: int
    total_pores: int
    level1_confidence: float
    level2_confidence: float
    level3_confidence: float
    
    # Metadados
    image_hash: str
    process_date: str
    expert_name: str
    expert_id: str


@dataclass
class ChemicalAnalysis:
    """Análise química da impressão"""
    sex_probability: Dict[str, float]
    age_estimate: str
    smoking_detected: bool
    drug_detected: bool
    time_stamp: str
    oxidation_level: float
    temperature: float
    humidity: float


@dataclass
class LegalFramework:
    """Framework legal aplicável"""
    jurisdiction: str  # 'PT/PT' or 'EN/US'
    ai_act_compliant: bool
    article_cited: str
    standard_reference: str
    privacy_compliant: bool


class ZephyrReportGenerator:
    """Gerador de relatórios periciais do ZEPHYR"""
    
    def __init__(self, legal_mode: str = 'PT/PT'):
        """Inicializa o gerador de relatórios"""
        self.legal_mode = legal_mode
        self.framework = self.load_legal_framework(legal_mode)
        self.output_dir = Path('./output/')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Gerador de relatórios ZEPHYR v{VERSION}")
        logger.info(f"Modo Legal: {legal_mode}")
    
    def load_legal_framework(self, mode: str) -> Dict:
        """Carrega o framework legal apropriado"""
        framework_file = f'./localization/{mode.lower().replace("/", "_")}_legal_framework.json'
        
        if Path(framework_file).exists():
            with open(framework_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Framework padrão
            if mode == 'PT/PT':
                return {
                    'jurisdiction': 'Portugal/UE',
                    'ai_act_compliant': True,
                    'cpp_article': 'Art. 163º CPP',
                    'privacy_law': 'Lei 59/2019 (RGPD Penal)',
                    'cybersecurity': 'DL 125/2025 (NIS2)',
                    'report_title': 'Parecer Técnico Forense',
                    'language': 'Português'
                }
            else:
                return {
                    'jurisdiction': 'Estados Unidos',
                    'daubert_compliant': True,
                    'federal_rules': 'Federal Rules of Evidence',
                    'nist_standard': 'NIST SP 500-334',
                    'amendment': '4ª Emenda',
                    'report_title': 'Forensic Expert Report',
                    'language': 'Inglês'
                }
    
    def generate_pdf(self, match_data: FingerprintMatch, 
                     chemical_data: Optional[ChemicalAnalysis] = None,
                     legal_data: Optional[LegalFramework] = None) -> str:
        """
        Gera um relatório pericial em PDF
        
        Args:
            match_data: Dados da correspondência
            chemical_data: Dados da análise química (opcional)
            legal_data: Dados do framework legal (opcional)
            
        Returns:
            Caminho para o ficheiro PDF gerado
        """
        logger.info(f"Gerando relatório para caso: {match_data.case_id}")
        
        # Preparar dados para o relatório
        report_data = {
            'case_id': match_data.case_id,
            'subject': {
                'id': match_data.subject_id,
                'name': match_data.subject_name
            },
            'match': {
                'score': match_data.confidence_score,
                'type': match_data.match_type,
                'minutiae_matched': match_data.minutiae_matched,
                'total_minutiae': match_data.total_minutiae,
                'pores_matched': match_data.pores_matched,
                'total_pores': match_data.total_pores
            },
            'confidence_levels': {
                'level1': match_data.level1_confidence,
                'level2': match_data.level2_confidence,
                'level3': match_data.level3_confidence
            },
            'metadata': {
                'image_hash': match_data.image_hash,
                'process_date': match_data.process_date,
                'expert': {
                    'name': match_data.expert_name,
                    'id': match_data.expert_id
                }
            },
            'legal': self.framework if not legal_data else asdict(legal_data),
            'chemical': asdict(chemical_data) if chemical_data else None,
            'generated_at': datetime.now().isoformat(),
            'system_version': VERSION
        }
        
        # Gerar ficheiro PDF
        filename = f"RELATORIO_PERICIAL_{match_data.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        try:
            # Utilizando reportlab para gerar PDF
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            from reportlab.pdfgen import canvas
            
            # Criar o documento
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            )
            
            elements = []
            
            # Título
            elements.append(Paragraph("RELATÓRIO TÉCNICO PERICIAL", title_style))
            elements.append(Paragraph("ZERO ENTROPY FINGERPRINT HYBRID ENGINE", title_style))
            elements.append(Spacer(1, 20))
            
            # Identificação
            elements.append(Paragraph("1. IDENTIFICAÇÃO DO PROCESSO", heading_style))
            elements.append(Paragraph(f"<b>Processo Nº:</b> {match_data.case_id}", normal_style))
            elements.append(Paragraph(f"<b>Data do Relatório:</b> {match_data.process_date}", normal_style))
            elements.append(Paragraph(f"<b>Perito(a):</b> {match_data.expert_name}", normal_style))
            elements.append(Paragraph(f"<b>ID do Perito(a):</b> {match_data.expert_id}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Sumário Executivo
            elements.append(Paragraph("2. SUMÁRIO EXECUTIVO", heading_style))
            
            match_text = "CORRESPONDÊNCIA CONFIRMADA" if match_data.match_type == 'positive' else "CORRESPONDÊNCIA NEGATIVA"
            elements.append(Paragraph(f"<b>Resultado:</b> {match_text}", normal_style))
            elements.append(Paragraph(f"<b>Score de Confiança:</b> {match_data.confidence_score:.5f}%", normal_style))
            elements.append(Paragraph(f"<b>Minúcias Correspondentes:</b> {match_data.minutiae_matched}/{match_data.total_minutiae}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Níveis de Certeza
            elements.append(Paragraph("3. NÍVEIS DE CERTEZA", heading_style))
            
            table_data = [
                ['Nível', 'Descrição', 'Valor'],
                ['N1', 'Fluxo de Cristas', f"{match_data.level1_confidence:.4f}%"],
                ['N2', 'Minúcias', f"{match_data.level2_confidence:.4f}%"],
                ['N3', 'Poros', f"{match_data.level3_confidence:.4f}%"],
                ['Final', 'Score Combinado', f"{match_data.confidence_score:.4f}%"]
            ]
            
            table = Table(table_data, colWidths=[80, 200, 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # Detalhes da Análise
            elements.append(Paragraph("4. ANÁLISE DETALHADA", heading_style))
            elements.append(Paragraph(f"<b>Total de Minúcias Identificadas:</b> {match_data.total_minutiae}", normal_style))
            elements.append(Paragraph(f"<b>Minúcias Correspondentes:</b> {match_data.minutiae_matched}", normal_style))
            elements.append(Paragraph(f"<b>Taxa de Correspondência:</b> {(match_data.minutiae_matched/match_data.total_minutiae*100):.2f}%", normal_style))
            elements.append(Spacer(1, 12))
            
            # Análise Química (se disponível)
            if chemical_data:
                elements.append(Paragraph("5. ANÁLISE QUÍMICA E TEMPORAL", heading_style))
                elements.append(Paragraph(f"<b>Sexo (Probabilidade):</b> Masculino ({chemical_data.sex_probability.get('male', 0):.1f}%)", normal_style))
                elements.append(Paragraph(f"<b>Idade Estimada:</b> {chemical_data.age_estimate}", normal_style))
                elements.append(Paragraph(f"<b>Fumador:</b> {'Sim' if chemical_data.smoking_detected else 'Não'} ", normal_style))
                elements.append(Paragraph(f"<b>Datação:</b> {chemical_data.time_stamp}", normal_style))
                elements.append(Spacer(1, 12))
            
            # Enquadramento Legal
            elements.append(Paragraph("6. ENQUADRAMENTO LEGAL", heading_style))
            elements.append(Paragraph(f"<b>Jurisdição:</b> {self.framework.get('jurisdiction', 'N/A')}", normal_style))
            elements.append(Paragraph(f"<b>Conformidade AI Act:</b> {'Sim' if self.framework.get('ai_act_compliant', False) else 'Não'}", normal_style))
            elements.append(Paragraph(f"<b>Referência Legal:</b> {self.framework.get('cpp_article', self.framework.get('federal_rules', 'N/A'))}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Conclusão
            elements.append(Paragraph("7. PARECER FINAL", heading_style))
            conclusion_text = """
            Com base nas análises realizadas, na metodologia científica aplicada
            e nos resultados obtidos, conclui-se com elevado grau de certeza
            """
            if match_data.match_type == 'positive':
                conclusion_text += f"({match_data.confidence_score:.4f}%)"
                conclusion_text += f" que a impressão digital analisada corresponde ao indivíduo {match_data.subject_name}."
            else:
                conclusion_text += f"({match_data.confidence_score:.4f}%)"
                conclusion_text += f" que a impressão digital analisada NÃO corresponde ao indivíduo {match_data.subject_name}."
            
            elements.append(Paragraph(conclusion_text, normal_style))
            elements.append(Spacer(1, 20))
            
            # Assinaturas
            elements.append(Paragraph("8. ASSINATURAS", heading_style))
            elements.append(Paragraph(f"<b>Perito(a) Responsável:</b>", normal_style))
            elements.append(Paragraph(f"{match_data.expert_name}", normal_style))
            elements.append(Paragraph(f"ID: {match_data.expert_id}", normal_style))
            elements.append(Paragraph(f"Data: {match_data.process_date}", normal_style))
            elements.append(Paragraph("Assinatura: [Assinatura Digital]", normal_style))
            elements.append(Spacer(1, 20))
            
            # Código de Verificação
            verification_hash = hashlib.sha3_256(
                f"{match_data.case_id}{match_data.confidence_score}{match_data.process_date}".encode()
            ).hexdigest()[:16]
            
            elements.append(Paragraph(f"<b>Código de Verificação:</b> ZPH-{match_data.case_id}-{verification_hash.upper()}", normal_style))
            elements.append(Paragraph(f"<b>Hash Final:</b> {hashlib.sha3_256(str(report_data).encode()).hexdigest().upper()}", normal_style))
            
            # Construir PDF
            doc.build(elements)
            
            logger.info(f"✅ Relatório gerado: {filepath}")
            return str(filepath)
            
        except ImportError:
            logger.warning("⚠️ ReportLab não instalado. Gerando relatório em formato texto...")
            return self.generate_text_report(match_data, chemical_data)
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF: {e}")
            return self.generate_text_report(match_data, chemical_data)
    
    def generate_text_report(self, match_data: FingerprintMatch,
                            chemical_data: Optional[ChemicalAnalysis] = None) -> str:
        """
        Gera relatório em formato texto (fallback)
        """
        filename = f"RELATORIO_PERICIAL_{match_data.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.output_dir / filename
        
        content = f"""
========================================
RELATÓRIO TÉCNICO PERICIAL
ZEPHYR - Zero Entropy Fingerprint Hybrid Engine
========================================

CASO: {match_data.case_id}
DATA: {match_data.process_date}
PERITO: {match_data.expert_name} (ID: {match_data.expert_id})

RESULTADO: {match_data.match_type.upper()}
SCORE DE CONFIANÇA: {match_data.confidence_score:.4f}%

MINÚCIAS:
  - Correspondentes: {match_data.minutiae_matched}
  - Total: {match_data.total_minutiae}
  - Taxa: {(match_data.minutiae_matched/match_data.total_minutiae*100):.2f}%

NÍVEIS DE CERTEZA:
  N1 (Cristas): {match_data.level1_confidence:.4f}%
  N2 (Minúcias): {match_data.level2_confidence:.4f}%
  N3 (Poros): {match_data.level3_confidence:.4f}%

INDIVÍDUO:
  ID: {match_data.subject_id}
  Nome: {match_data.subject_name}

"""
        
        if chemical_data:
            content += f"""
ANÁLISE QUÍMICA:
  Sexo: Masculino ({chemical_data.sex_probability.get('male', 0):.1f}%)
  Idade: {chemical_data.age_estimate}
  Fumador: {'Sim' if chemical_data.smoking_detected else 'Não'}
  Drogas: {'Sim' if chemical_data.drug_detected else 'Não'}
  Datação: {chemical_data.time_stamp}
"""
        
        content += f"""
ENQUADRAMENTO LEGAL:
  Jurisdição: {self.framework.get('jurisdiction', 'N/A')}
  AI Act: {'Sim' if self.framework.get('ai_act_compliant', False) else 'Não'}
  Referência: {self.framework.get('cpp_article', self.framework.get('federal_rules', 'N/A'))}

CÓDIGO DE VERIFICAÇÃO: ZPH-{match_data.case_id}-{hashlib.sha3_256(f"{match_data.case_id}{match_data.confidence_score}".encode()).hexdigest()[:16].upper()}

========================================
FIM DO RELATÓRIO
========================================
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Relatório texto gerado: {filepath}")
        return str(filepath)
    
    def generate_json(self, match_data: FingerprintMatch,
                     chemical_data: Optional[ChemicalAnalysis] = None) -> str:
        """
        Gera relatório em formato JSON (para integração)
        """
        data = {
            'case': asdict(match_data),
            'legal_framework': self.framework,
            'system': {
                'name': SYSTEM_NAME,
                'version': VERSION,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        if chemical_data:
            data['chemical_analysis'] = asdict(chemical_data)
        
        filename = f"RELATORIO_{match_data.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ JSON gerado: {filepath}")
        return str(filepath)


def parse_arguments():
    """Processa os argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description=f"{SYSTEM_NAME} - Gerador de Relatórios Forenses"
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['PT/PT', 'EN/US'],
        default='PT/PT',
        help='Modo legal do sistema'
    )
    parser.add_argument(
        '--case-id',
        type=str,
        required=True,
        help='ID do caso'
    )
    parser.add_argument(
        '--subject-id',
        type=str,
        required=True,
        help='ID do indivíduo'
    )
    parser.add_argument(
        '--subject-name',
        type=str,
        required=True,
        help='Nome do indivíduo'
    )
    parser.add_argument(
        '--score',
        type=float,
        default=99.9999,
        help='Score de confiança'
    )
    parser.add_argument(
        '--match-type',
        type=str,
        choices=['positive', 'negative', 'inconclusive'],
        default='positive',
        help='Tipo de correspondência'
    )
    parser.add_argument(
        '--expert-name',
        type=str,
        default='Dr. João Silva',
        help='Nome do perito'
    )
    parser.add_argument(
        '--expert-id',
        type=str,
        default='PER-2026-0042-PJ',
        help='ID do perito'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['pdf', 'text', 'json'],
        default='pdf',
        help='Formato de saída'
    )
    return parser.parse_args()


def main():
    """Função principal"""
    args = parse_arguments()
    
    # Criar dados de exemplo
    match_data = FingerprintMatch(
        case_id=args.case_id,
        subject_id=args.subject_id,
        subject_name=args.subject_name,
        confidence_score=args.score,
        match_type=args.match_type,
        minutiae_matched=38,
        total_minutiae=41,
        pores_matched=142,
        total_pores=156,
        level1_confidence=99.9999,
        level2_confidence=99.9999,
        level3_confidence=99.9998,
        image_hash=hashlib.sha3_256(f"{args.case_id}_image".encode()).hexdigest(),
        process_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        expert_name=args.expert_name,
        expert_id=args.expert_id
    )
    
    # Criar dados químicos de exemplo
    chemical_data = ChemicalAnalysis(
        sex_probability={'male': 87.2, 'female': 12.8},
        age_estimate='35-45 anos',
        smoking_detected=True,
        drug_detected=False,
        time_stamp='2026-06-18 22:00 - 00:00',
        oxidation_level=0.23,
        temperature=22.0,
        humidity=60.0
    )
    
    # Gerar relatório
    generator = ZephyrReportGenerator(args.mode)
    
    if args.format == 'pdf':
        generator.generate_pdf(match_data, chemical_data)
    elif args.format == 'json':
        generator.generate_json(match_data, chemical_data)
    else:
        generator.generate_text_report(match_data, chemical_data)
    
    logger.info("✅ Relatório gerado com sucesso!")


if __name__ == "__main__":
    main()