"""
Question Extractor - Identificação Formal de Perguntas no Contexto FCJ

Responsabilidade:
- Extrair PERGUNTAS (não apenas campos preenchíveis)
- Definir formalmente semântica de pergunta para FCJ
- Associar perguntas a blocos de resposta
- Preservar ordem e contexto

Modelo semântico:
- Uma PERGUNTA é um solicitação de reflexão/preenchimento
- Pode aparecer como: pergunta direta, instrução, solicitação
- Normalmente diferenciada visualmente (cor, borda, tamanho)
- Localizada: acima OU à esquerda de bloco de resposta
"""

from __future__ import annotations
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Question:
    """Representa uma pergunta no contexto FCJ"""
    
    # Identificação
    field_id: str  # hash determinístico
    sheet_index: int  # índice real da aba (0, 1, 2...)
    sheet_name: str
    
    # Localização
    cell_range: str  # onde a pergunta está escrita
    row: int  # linha inicial da pergunta
    column: int  # coluna inicial da pergunta
    
    # Contexto
    section_name: Optional[str]  # nome da seção (título)
    section_index: int  # ordem da seção dentro da aba
    
    # Conteúdo
    question_text: str  # texto exato da pergunta
    
    # Semântica
    inferred_type: str  # text_short, text_long, number, date, choice
    
    # Ordem (CRÍTICO)
    order_index_sheet: int  # ordem dentro da aba (1, 2, 3...)
    order_index_global: int  # ordem global na trilha inteira
    
    # Resposta
    answer_cell_range: Optional[str]  # onde a resposta deve ir
    answer_row_start: Optional[int]
    answer_row_end: Optional[int]
    
    # Metadados
    required: bool = True
    example_value: Optional[str] = None
    validation_type: Optional[str] = None
    source_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.source_metadata is None:
            self.source_metadata = {}
    
    def to_dict(self, template_id: str) -> Dict[str, Any]:
        """Converte para dict para persistência"""
        return {
            "template_id": template_id,
            "field_id": self.field_id,
            "sheet_index": self.sheet_index,
            "sheet_name": self.sheet_name,
            "section_name": self.section_name,
            "section_index": self.section_index,
            "question_text": self.question_text,
            "cell_range": self.cell_range,
            "inferred_type": self.inferred_type,
            "answer_cell_range": self.answer_cell_range,
            "order_index_sheet": self.order_index_sheet,
            "order_index_global": self.order_index_global,
            "required": self.required,
            "example_value": self.example_value,
            "validation_type": self.validation_type,
            "source_metadata": self.source_metadata,
        }


class QuestionExtractor:
    """
    Extrai PERGUNTAS formais do snapshot respeitando semântica FCJ
    
    Algoritmo:
    1. Por aba (na ordem real): 
       - Identificar seções (títulos horizontais destacados)
       - Identificar perguntas (texto de instrução/solicitação)
       - Associar pergunta a bloco de resposta
       - Respeitar ordem vertical rigorosamente
    2. Computar order_index global
    """
    
    # Padrões que indicam PERGUNTA (não título)
    QUESTION_KEYWORDS = [
        r"qual\b",
        r"quais\b",
        r"o que\b",
        r"como\b",
        r"por que\b",
        r"quando\b",
        r"onde\b",
        r"descreva\b",
        r"liste\b",
        r"explique\b",
        r"defina\b",
        r"identifique\b",
        r"escreva\b",
        r"preencha\b",
        r"indique\b",
        r"detalhe\b",
    ]
    
    # Padrões que indicam SEÇÃO (não pergunta)
    SECTION_KEYWORDS = [
        r"^(Fase|Phase|Etapa|Stage|Bloco|Block)",
        r"^(Título|Title|Seção|Section)",
        r"^(Capítulo|Chapter)",
        r"^(Módulo|Module)",
    ]
    
    # Padrões de exclusão (não é pergunta)
    EXCLUDE_PATTERNS = [
        r"exemplo",
        r"\bex\b[:.)]",
        r"\(ex\)",
        r"sample",
        r"demo",
        r"note:",
        r"observação:",
        r"^[\[\{]",  # começa com bracket
    ]
    
    def __init__(self):
        self.logger = logger
    
    def extract(self, snapshot: Dict[str, Any]) -> Tuple[List[Question], Dict[str, Any]]:
        """
        Extrai todas as perguntas preservando ordem
        
        Args:
            snapshot: Snapshot JSON completo
            
        Returns:
            (questions: List[Question], audit: Dict com estatísticas)
            
        Raises:
            ValueError: Se alguma aba não tiver perguntas/respostas ou houver ambiguidade
        """
        questions: List[Question] = []
        audit = {
            "sheets_analyzed": 0,
            "total_questions": 0,
            "total_sections": 0,
            "coverage_by_sheet": {},
            "errors": [],
        }
        
        sheets = snapshot.get("sheets", [])
        global_order = 0
        
        # ✅ Iterar EXATAMENTE na ordem das sheets
        for sheet_index, sheet in enumerate(sheets):
            sheet_name = sheet.get("name", f"Sheet_{sheet_index}")
            
            self.logger.info(f"📖 Processando aba [{sheet_index}]: '{sheet_name}'")
            
            try:
                sheet_questions = self._extract_sheet_questions(
                    sheet=sheet,
                    sheet_index=sheet_index,
                    sheet_name=sheet_name,
                    global_order_base=global_order
                )
                
                # ✅ Validar cobertura: deve haver perguntas
                if not sheet_questions:
                    error = f"Aba '{sheet_name}' não tem perguntas detectadas"
                    self.logger.error(f"  ❌ {error}")
                    audit["errors"].append(error)
                    raise ValueError(error)
                
                questions.extend(sheet_questions)
                global_order += len(sheet_questions)
                
                audit["coverage_by_sheet"][sheet_name] = {
                    "questions_found": len(sheet_questions),
                    "order_index_start": global_order - len(sheet_questions),
                    "order_index_end": global_order - 1,
                }
                
                self.logger.info(f"  ✅ {len(sheet_questions)} perguntas extraídas")
                
            except ValueError as e:
                audit["errors"].append(f"Aba '{sheet_name}': {str(e)}")
                raise
            
            audit["sheets_analyzed"] += 1
        
        audit["total_questions"] = len(questions)
        
        # ✅ Validar ordem global
        for i, q in enumerate(questions):
            if q.order_index_global != i:
                raise ValueError(
                    f"Ordem global inconsistente: question '{q.question_text[:30]}' "
                    f"esperava order_index_global={i}, tem {q.order_index_global}"
                )
        
        self.logger.info(f"✅ EXTRAÇÃO COMPLETA: {len(questions)} perguntas em {audit['sheets_analyzed']} abas")
        
        return questions, audit
    
    def _extract_sheet_questions(
        self,
        sheet: Dict[str, Any],
        sheet_index: int,
        sheet_name: str,
        global_order_base: int
    ) -> List[Question]:
        """Extrai perguntas de uma sheet respeitando ordem vertical"""
        
        cells = sheet.get("cells", [])
        merged_cells = sheet.get("merged_cells", [])
        
        # 1. Ordenar células por (row, col) para leitura top-to-bottom
        cells_sorted = sorted(
            cells,
            key=lambda c: (c.get("row", 0), c.get("column", 0))
        )
        
        # 2. Identificar seções (títulos destacados)
        sections = self._identify_sections(cells_sorted)
        self.logger.info(f"    Seções identificadas: {len(sections)}")
        
        # 3. Identificar perguntas e associar a respostas
        questions = []
        sheet_order = 0
        
        for cell_idx, cell in enumerate(cells_sorted):
            row = cell.get("row")
            col = cell.get("column")
            value = cell.get("value")
            coord = cell.get("coordinate")
            
            # Verificar se é pergunta
            if not self._is_question(value, cell):
                continue
            
            # Encontrar seção que contém esta pergunta
            section = self._find_section_for_cell(row, sections)
            section_name = section.get("name") if section else None
            section_index = section.get("index") if section else -1
            
            # Encontrar bloco de resposta correspondente
            answer_range = self._find_answer_block(
                question_row=row,
                question_col=col,
                cells_sorted=cells_sorted,
                merged_cells=merged_cells
            )
            
            if not answer_range:
                self.logger.warning(
                    f"    ⚠️ Pergunta sem bloco de resposta: '{value[:50]}' @ {coord}"
                )
                # Não interromper, apenas avisar
            
            # Criar pergunta
            question = Question(
                field_id=self._compute_field_id(sheet_name, row, col, value),
                sheet_index=sheet_index,
                sheet_name=sheet_name,
                cell_range=coord,
                row=row,
                column=col,
                section_name=section_name,
                section_index=section_index,
                question_text=str(value).strip(),
                inferred_type=self._infer_type(cell),
                order_index_sheet=sheet_order,
                order_index_global=global_order_base + sheet_order,
                answer_cell_range=answer_range.get("range") if answer_range else None,
                answer_row_start=answer_range.get("row_start") if answer_range else None,
                answer_row_end=answer_range.get("row_end") if answer_range else None,
                required=True,
                source_metadata={
                    "detection_method": "question_extractor",
                    "section": section_name,
                },
            )
            
            questions.append(question)
            sheet_order += 1
            
            self.logger.debug(
                f"      📝 [{sheet_order}] {value[:50][:50]}... "
                f"@ {coord} → {answer_range}"
            )
        
        return questions
    
    def _is_question(self, value: Any, cell: Dict[str, Any]) -> bool:
        """Verifica formalmente se é uma pergunta (não título/exemplo)"""
        
        if not value:
            return False
        
        value_str = str(value).strip().lower()
        
        # Excluir padrões
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, value_str):
                return False
        
        # Excluir muito curto
        if len(value_str) < 5:
            return False
        
        # Verificar se é título (muito grande + bold)
        style = cell.get("style", {})
        font = style.get("font", {})
        if font.get("size", 0) >= 14 and font.get("bold"):
            # Pode ser título, não pergunta
            # A menos que tenha palavra-chave de pergunta
            pass
        
        # Criterio: tem palavra-chave de pergunta
        has_keyword = any(
            re.search(pattern, value_str)
            for pattern in self.QUESTION_KEYWORDS
        )
        
        return has_keyword
    
    def _identify_sections(self, cells_sorted: List[Dict]) -> List[Dict[str, Any]]:
        """Identifica seções (títulos horizontais destacados)"""
        
        sections = []
        section_index = 0
        
        for cell in cells_sorted:
            value = cell.get("value")
            if not value:
                continue
            
            value_str = str(value).strip()
            
            # Verificar se é título de seção
            is_section = False
            for pattern in self.SECTION_KEYWORDS:
                if re.search(pattern, value_str, re.IGNORECASE):
                    is_section = True
                    break
            
            # Ou: grande + bold + cor
            if not is_section:
                style = cell.get("style", {})
                font = style.get("font", {})
                fill = style.get("fill", {})
                
                is_section = (
                    font.get("size", 0) >= 14 and
                    font.get("bold") and
                    fill.get("fgColor")  # tem cor
                )
            
            if is_section:
                sections.append({
                    "index": section_index,
                    "name": value_str,
                    "row_start": cell.get("row"),
                    "row_end": None,  # será atualizado pelo próximo
                })
                section_index += 1
        
        # Atualizar row_end
        for i in range(len(sections) - 1):
            sections[i]["row_end"] = sections[i + 1]["row_start"] - 1
        if sections:
            sections[-1]["row_end"] = 9999
        
        return sections
    
    def _find_section_for_cell(
        self,
        row: int,
        sections: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Encontra seção que contém esta célula"""
        
        for section in sections:
            if (section.get("row_start") <= row <= (section.get("row_end") or 9999)):
                return section
        
        return None
    
    def _find_answer_block(
        self,
        question_row: int,
        question_col: int,
        cells_sorted: List[Dict],
        merged_cells: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Encontra bloco de resposta correspondente à pergunta
        
        Estratégia:
        - Procura abaixo (prioridade)
        - Procura à direita
        - Não pode conter fórmula
        """
        
        # Procurar abaixo (mesma coluna, linhas seguintes)
        for cell in cells_sorted:
            row = cell.get("row")
            col = cell.get("column")
            value = cell.get("value")
            
            if row > question_row and col == question_col:
                # Validar que é célula de resposta (vazia ou exemple)
                if value is None or (isinstance(value, str) and len(value) < 100):
                    # Expandir se for merged
                    coord = cell.get("coordinate")
                    for merged in merged_cells:
                        if coord in merged:
                            return {
                                "range": merged,
                                "row_start": row,
                                "row_end": row,  # aprox
                            }
                    
                    return {
                        "range": coord,
                        "row_start": row,
                        "row_end": row,
                    }
        
        return None
    
    def _compute_field_id(
        self,
        sheet_name: str,
        row: int,
        col: int,
        question_text: str
    ) -> str:
        """Computa field_id determinístico"""
        
        hashable = f"{sheet_name}|{row}|{col}|{question_text}"
        return hashlib.sha1(hashable.encode("utf-8")).hexdigest()[:16]
    
    def _infer_type(self, cell: Dict[str, Any]) -> str:
        """Infere tipo de resposta esperada"""
        
        # Validação de dados?
        dv = cell.get("data_validation")
        if dv:
            dv_type = dv.get("type", "").lower()
            if dv_type in ("list", "listvalid"):
                return "choice"
        
        # Formato de data?
        fmt = cell.get("number_format", "").lower()
        if any(x in fmt for x in ["dd", "mm", "yy", "date"]):
            return "date"
        
        # Numérico?
        dt = cell.get("data_type")
        if dt in ("n", "f"):
            return "number"
        
        # Default
        return "text_short"
    
    def validate_coverage(
        self,
        questions: List[Question],
        snapshot: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Valida que todas as perguntas possíveis foram extraídas
        
        Returns:
            (valid: bool, errors: List[str])
        """
        
        errors = []
        
        # Validar que cada aba tem perguntas
        for sheet_idx, sheet in enumerate(snapshot.get("sheets", [])):
            sheet_questions = [q for q in questions if q.sheet_index == sheet_idx]
            if not sheet_questions:
                errors.append(
                    f"Aba '{sheet.get('name')}' [idx={sheet_idx}] não tem perguntas"
                )
        
        # Validar que order_index_global é contíguo
        if questions:
            for i, q in enumerate(questions):
                if q.order_index_global != i:
                    errors.append(
                        f"Order global quebrada: pergunta {i} tem order_index_global={q.order_index_global}"
                    )
        
        return len(errors) == 0, errors
