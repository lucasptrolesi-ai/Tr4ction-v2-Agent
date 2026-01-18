"""
Fillable Area Detector - Detecção inteligente de áreas preenchíveis
===================================================================

RESPONSABILIDADE:
Identificar TODAS as áreas que devem ser preenchidas pelo founder,
sem hardcode, baseado exclusivamente no snapshot JSON.

HEURÍSTICAS CORE:
1. Agrupamento em blocos lógicos (merged ranges + adjacentes)
2. Inferência de labels por proximidade
3. Tipagem semântica (choice/date/text/number)
4. Normalização FCJ (phase/cycle/order)
5. Exclusão de exemplos e títulos

GARANTIAS:
- Não perder campos obrigatórios
- Não criar falsos positivos
- Estabilidade determinística (field_id)
"""

from __future__ import annotations
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FillableFieldCandidate:
    """
    Representa um campo preenchível detectado
    """
    
    def __init__(
        self,
        sheet: str,
        cell_range: str,
        label: Optional[str],
        inferred_type: str,
        required: bool,
        example_value: Optional[str],
        phase: Optional[str],
        order_index: int,
        source_metadata: Dict[str, Any]
    ):
        self.sheet = sheet
        self.cell_range = cell_range
        self.label = label
        self.inferred_type = inferred_type
        self.required = required
        self.example_value = example_value
        self.phase = phase
        self.order_index = order_index
        self.source_metadata = source_metadata

    def to_dict(self, template_id: str) -> Dict[str, Any]:
        """Converte para dict com field_id estável"""
        stable_hash = hashlib.sha1(
            f"{self.sheet}|{self.cell_range}|{self.label or ''}".encode("utf-8")
        ).hexdigest()[:16]
        
        return {
            "template_id": template_id,
            "field_id": stable_hash,
            "sheet_name": self.sheet,
            "cell_range": self.cell_range,
            "label": self.label,
            "inferred_type": self.inferred_type,
            "required": self.required,
            "example_value": self.example_value,
            "phase": self.phase,
            "order_index": self.order_index,
            "source_metadata": self.source_metadata,
        }


class FillableAreaDetector:
    """
    Detector inteligente de áreas preenchíveis em templates Excel
    """
    
    # Padrões de exclusão
    EXAMPLE_PATTERNS = [
        r"exemplo",
        r"\bex\b[:.)]",
        r"\(ex\)",
        r"sample",
        r"demo",
    ]
    
    def detect(self, snapshot: Dict[str, Any]) -> List[FillableFieldCandidate]:
        """
        Detecta áreas preenchíveis no snapshot
        
        Args:
            snapshot: Snapshot JSON completo
            
        Returns:
            Lista de candidatos detectados
        """
        candidates: List[FillableFieldCandidate] = []
        sheets = snapshot.get("sheets", [])
        
        for s_index, sheet in enumerate(sheets):
            name = sheet.get("name")
            merged = sheet.get("merged_cells", [])
            cells = sheet.get("cells", [])
            validations = sheet.get("data_validations", [])
            
            logger.info(f"Analisando sheet '{name}': {len(cells)} células, {len(merged)} merged")
            
            # 1. Processar merged ranges primeiro (prioridade)
            processed_coords: Set[str] = set()
            for rng in merged:
                candidate = self._analyze_merged_range(
                    rng, cells, validations, name, s_index
                )
                if candidate:
                    candidates.append(candidate)
                    # Marcar coordenadas como processadas
                    for coord in self._expand_range(rng):
                        processed_coords.add(coord)
            
            # 2. Processar células individuais não processadas
            for cell in cells:
                coord = cell.get("coordinate")
                if coord in processed_coords:
                    continue
                
                candidate = self._analyze_single_cell(
                    cell, cells, validations, name, s_index
                )
                if candidate:
                    candidates.append(candidate)
                    processed_coords.add(coord)
        
        # Ordenar por order_index
        candidates.sort(key=lambda c: c.order_index)
        
        logger.info(f"✓ Detectados {len(candidates)} campos preenchíveis")
        
        return candidates

    def _analyze_merged_range(
        self,
        rng: str,
        cells: List[Dict],
        validations: List[Dict],
        sheet_name: str,
        sheet_index: int
    ) -> Optional[FillableFieldCandidate]:
        """
        Analisa um merged range como candidato
        
        Returns:
            Candidato ou None se não for preenchível
        """
        # Buscar primeira célula do range
        first_coord = rng.split(":")[0]
        cell = next((c for c in cells if c.get("coordinate") == first_coord), None)
        
        if not cell:
            return None
        
        # Regras de exclusão
        if not self._is_fillable_candidate(cell):
            return None
        
        # Label: buscar próximo
        label = self._find_label_near_coordinate(first_coord, cells)
        
        # Example value: capturar do range se existir
        example = self._extract_example_from_cells(self._expand_range(rng), cells)
        
        # Tipo inferido
        inferred_type = self._infer_type(cell, rng, validations)
        
        # Phase
        phase = self._infer_phase(sheet_name, label)
        
        # Order
        order_index = self._compute_order_index(first_coord, sheet_index)
        
        # Metadata
        metadata = {
            "is_merged": True,
            "has_validation": self._range_has_validation(rng, validations),
            "detection_method": "merged_range",
            "cell_count": len(self._expand_range(rng)),
        }
        
        return FillableFieldCandidate(
            sheet=sheet_name,
            cell_range=rng,
            label=label,
            inferred_type=inferred_type,
            required=True,
            example_value=example,
            phase=phase,
            order_index=order_index,
            source_metadata=metadata
        )

    def _analyze_single_cell(
        self,
        cell: Dict,
        cells: List[Dict],
        validations: List[Dict],
        sheet_name: str,
        sheet_index: int
    ) -> Optional[FillableFieldCandidate]:
        """
        Analisa célula individual como candidato
        
        Returns:
            Candidato ou None se não for preenchível
        """
        if not self._is_fillable_candidate(cell):
            return None
        
        coord = cell.get("coordinate")
        
        # Label
        label = self._find_label_near_coordinate(coord, cells)
        
        # Example
        value = cell.get("value")
        example = str(value) if value and len(str(value)) < 50 else None
        if example and self._is_example_text(example):
            example = None  # Não usar exemplos como valor
        
        # Tipo
        inferred_type = self._infer_type(cell, coord, validations)
        
        # Phase
        phase = self._infer_phase(sheet_name, label)
        
        # Order
        order_index = self._compute_order_index(coord, sheet_index)
        
        # Metadata
        metadata = {
            "is_merged": False,
            "has_validation": self._cell_has_validation(coord, validations),
            "detection_method": "single_cell",
            "data_type": cell.get("data_type"),
        }
        
        return FillableFieldCandidate(
            sheet=sheet_name,
            cell_range=coord,
            label=label,
            inferred_type=inferred_type,
            required=True,
            example_value=example,
            phase=phase,
            order_index=order_index,
            source_metadata=metadata
        )

    def _is_fillable_candidate(self, cell: Dict) -> bool:
        """
        Verifica se célula é candidata a preenchível
        
        Regras de exclusão:
        - Tem fórmula
        - Título (fonte grande + bold + cor)
        - Exemplo explícito
        - Conteúdo muito longo
        """
        # Fórmulas = não preenchível
        if cell.get("formula"):
            return False
        
        # Estilo
        style = cell.get("style", {})
        font = style.get("font", {})
        fill = style.get("fill", {})
        
        # Título: bold + tamanho grande + fundo colorido
        is_title = (
            font.get("bold") and
            font.get("size", 0) >= 14 and
            self._has_colored_fill(fill)
        )
        if is_title:
            return False
        
        # Valor
        value = cell.get("value")
        if value:
            value_str = str(value)
            
            # Exemplo explícito
            if self._is_example_text(value_str):
                return False
            
            # Texto muito longo = não é campo
            if len(value_str) > 200:
                return False
        
        return True

    def _has_colored_fill(self, fill: Dict) -> bool:
        """Verifica se tem preenchimento colorido"""
        fg = fill.get("fgColor")
        if not fg or fg in ["FFFFFFFF", "00000000", None]:
            return False
        return True

    def _is_example_text(self, text: str) -> bool:
        """Verifica se texto é exemplo"""
        text_lower = text.lower()
        for pattern in self.EXAMPLE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _find_label_near_coordinate(
        self,
        coord: str,
        cells: List[Dict]
    ) -> Optional[str]:
        """
        Busca label mais próximo (acima ou à esquerda)
        
        Estratégia:
        - Procura em janela 3x3 acima e à esquerda
        - Ignora exemplos e células vazias
        - Retorna primeiro match válido
        """
        row, col = self._parse_coordinate(coord)
        
        candidates = []
        
        # Buscar acima (prioridade)
        for dr in range(1, 4):
            r = row - dr
            if r < 1:
                break
            
            target_coord = self._build_coordinate(r, col)
            match = next((c for c in cells if c.get("coordinate") == target_coord), None)
            
            if match:
                val = match.get("value")
                if val and isinstance(val, (str, int)):
                    text = str(val).strip()
                    if text and not self._is_example_text(text) and len(text) < 100:
                        candidates.append(text)
                        break
        
        # Buscar à esquerda se não encontrou acima
        if not candidates:
            for dc in range(1, 4):
                c = col - dc
                if c < 1:
                    break
                
                target_coord = self._build_coordinate(row, c)
                match = next((cell for cell in cells if cell.get("coordinate") == target_coord), None)
                
                if match:
                    val = match.get("value")
                    if val and isinstance(val, (str, int)):
                        text = str(val).strip()
                        if text and not self._is_example_text(text) and len(text) < 100:
                            candidates.append(text)
                            break
        
        return candidates[0] if candidates else None

    def _infer_type(
        self,
        cell: Dict,
        cell_range: str,
        validations: List[Dict]
    ) -> str:
        """
        Infere tipo semântico do campo
        
        Prioridades (SEM HARDCODE):
        1. Validation list -> choice
        2. Number format de data -> date
        3. Range grande -> text_long
        4. Data type numérico -> number
        5. Célula com currency -> number
        6. Default -> text_short
        """
        # 1. Validation list (maior prioridade)
        if self._range_has_validation(cell_range, validations):
            val_type = self._get_validation_type(cell_range, validations)
            if val_type and val_type.lower() in ("list", "listvalid"):
                logger.debug(f"  -> Tipo 'choice' inferido por validation list")
                return "choice"
        
        # 2. Format de data
        fmt = cell.get("number_format", "").lower() if cell.get("number_format") else ""
        if any(x in fmt for x in ["dd", "mm", "yy", "date", "time"]):
            logger.debug(f"  -> Tipo 'date' inferido por number_format: {fmt}")
            return "date"
        
        # 3. Range grande = text_long (para merged cells)
        if ":" in cell_range:
            area = self._compute_range_area(cell_range)
            if area >= 4:
                logger.debug(f"  -> Tipo 'text_long' inferido por área de merged cell: {area}")
                return "text_long"
        
        # 4. Data type numérico
        dt = cell.get("data_type")
        if dt in ("n", "f"):
            logger.debug(f"  -> Tipo 'number' inferido por data_type: {dt}")
            return "number"
        
        # 5. Currency format
        if fmt and any(x in fmt for x in ["$", "€", "currency", "accounting"]):
            logger.debug(f"  -> Tipo 'number' inferido por formato currency")
            return "number"
        
        # Default
        logger.debug(f"  -> Tipo 'text_short' (padrão)")
        return "text_short"
        
        # Range grande = text_long
        if ":" in cell_range:
            area = self._compute_range_area(cell_range)
            if area >= 4:
                return "text_long"
        
        # Data type
        dt = cell.get("data_type")
        if dt in ("n", "f"):
            return "number"
        
        return "text_short"

    def _infer_phase(self, sheet_name: str, label: Optional[str]) -> Optional[str]:
        """
        Infere phase FCJ pelo nome da sheet ou label
        
        Fases conhecidas:
        - ICP
        - Persona
        - SWOT
        - Journey/Funil
        - Metrics
        """
        text = f"{sheet_name} {label or ''}".lower()
        
        if "icp" in text or "ideal customer" in text:
            return "icp"
        if "persona" in text:
            return "persona"
        if "swot" in text:
            return "swot"
        if any(x in text for x in ["funil", "funnel", "jornada", "journey"]):
            return "journey"
        if any(x in text for x in ["metric", "métrica", "kpi", "okr"]):
            return "metrics"
        
        return None

    def _compute_order_index(self, coord: str, sheet_index: int) -> int:
        """
        Computa índice de ordenação estável
        
        Formula: sheet_index * 100000 + row * 1000 + col
        """
        row, col = self._parse_coordinate(coord)
        return sheet_index * 100000 + row * 1000 + col

    def _parse_coordinate(self, coord: str) -> Tuple[int, int]:
        """Parse A1 -> (row, col)"""
        m = re.match(r"([A-Z]+)(\d+)", coord)
        if not m:
            return (1, 1)
        col_letter, row_str = m.groups()
        return int(row_str), self._col_letter_to_num(col_letter)

    def _build_coordinate(self, row: int, col: int) -> str:
        """Build (row, col) -> A1"""
        return f"{self._col_num_to_letter(col)}{row}"

    def _col_letter_to_num(self, col: str) -> int:
        """A -> 1, Z -> 26, AA -> 27"""
        n = 0
        for ch in col:
            n = n * 26 + (ord(ch) - 64)
        return n

    def _col_num_to_letter(self, n: int) -> str:
        """1 -> A, 26 -> Z, 27 -> AA"""
        s = ""
        while n:
            n, r = divmod(n - 1, 26)
            s = chr(r + 65) + s
        return s

    def _expand_range(self, rng: str) -> List[str]:
        """Expande A1:B2 -> [A1, A2, B1, B2]"""
        if ":" not in rng:
            return [rng]
        
        start, end = rng.split(":")
        r1, c1 = self._parse_coordinate(start)
        r2, c2 = self._parse_coordinate(end)
        
        coords = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                coords.append(self._build_coordinate(r, c))
        
        return coords

    def _extract_example_from_cells(
        self,
        coords: List[str],
        cells: List[Dict]
    ) -> Optional[str]:
        """Extrai exemplo de um grupo de células"""
        for coord in coords:
            cell = next((c for c in cells if c.get("coordinate") == coord), None)
            if cell:
                val = cell.get("value")
                if val and len(str(val)) < 50 and not self._is_example_text(str(val)):
                    return str(val)
        return None

    def _range_has_validation(self, rng: str, validations: List[Dict]) -> bool:
        """Verifica se range tem validation"""
        for dv in validations:
            sqref = dv.get("sqref")
            if sqref and rng in str(sqref):
                return True
        return False

    def _cell_has_validation(self, coord: str, validations: List[Dict]) -> bool:
        """Verifica se célula tem validation"""
        return self._range_has_validation(coord, validations)

    def _get_validation_type(self, rng: str, validations: List[Dict]) -> Optional[str]:
        """Retorna tipo de validation"""
        for dv in validations:
            sqref = dv.get("sqref")
            if sqref and rng in str(sqref):
                return dv.get("type")
        return None

    def _compute_range_area(self, rng: str) -> int:
        """Calcula área de um range"""
        if ":" not in rng:
            return 1
        
        start, end = rng.split(":")
        r1, c1 = self._parse_coordinate(start)
        r2, c2 = self._parse_coordinate(end)
        
        rows = abs(r2 - r1) + 1
        cols = abs(c2 - c1) + 1
        
        return rows * cols
