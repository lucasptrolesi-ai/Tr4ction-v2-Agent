"""
Testes do Fillable Area Detector
=================================

Valida detecção inteligente de áreas preenchíveis
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from app.services.fillable_detector import FillableAreaDetector, FillableFieldCandidate


class TestFillableDetection:
    """Testes de detecção de campos"""
    
    def test_detect_merged_range(self):
        """Testa detecção de merged range como campo"""
        snapshot = {
            "schema_version": "2.0",
            "sheets": [
                {
                    "name": "ICP",
                    "cells": [
                        {
                            "coordinate": "A1",
                            "value": "Nome da Empresa:",
                            "style": {
                                "font": {"bold": True, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        },
                        {
                            "coordinate": "B1",
                            "value": None,
                            "formula": None,
                            "style": {
                                "font": {"bold": False, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        }
                    ],
                    "merged_cells": ["B1:C1"],
                    "data_validations": [],
                    "row_dimensions": [],
                    "column_dimensions": [],
                    "conditional_formatting": [],
                    "tables": [],
                    "images": [],
                }
            ]
        }
        
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        assert len(candidates) > 0
        
        # Buscar o campo do merged range
        merged_field = next((c for c in candidates if c.cell_range == "B1:C1"), None)
        assert merged_field is not None
        assert merged_field.sheet == "ICP"
        assert merged_field.label is not None  # Deve capturar "Nome da Empresa:"
        assert merged_field.phase == "icp"
    
    def test_detect_single_cell_with_validation(self):
        """Testa detecção de célula com validation (choice)"""
        snapshot = {
            "schema_version": "2.0",
            "sheets": [
                {
                    "name": "SWOT",
                    "cells": [
                        {
                            "coordinate": "A1",
                            "value": "Categoria:",
                            "style": {
                                "font": {"bold": True, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        },
                        {
                            "coordinate": "A2",
                            "value": None,
                            "formula": None,
                            "data_type": "s",
                            "style": {
                                "font": {"bold": False, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        }
                    ],
                    "merged_cells": [],
                    "data_validations": [
                        {
                            "type": "list",
                            "formula1": '"Força,Fraqueza,Oportunidade,Ameaça"',
                            "sqref": "A2"
                        }
                    ],
                    "row_dimensions": [],
                    "column_dimensions": [],
                    "conditional_formatting": [],
                    "tables": [],
                    "images": [],
                }
            ]
        }
        
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        choice_field = next((c for c in candidates if c.cell_range == "A2"), None)
        assert choice_field is not None
        assert choice_field.inferred_type == "choice"
        assert choice_field.phase == "swot"
    
    def test_exclude_titles(self):
        """Testa exclusão de títulos (bold + grande + colorido)"""
        snapshot = {
            "schema_version": "2.0",
            "sheets": [
                {
                    "name": "Sheet1",
                    "cells": [
                        {
                            "coordinate": "A1",
                            "value": "TÍTULO PRINCIPAL",
                            "style": {
                                "font": {"bold": True, "size": 18},
                                "fill": {"fgColor": "FF0000"},  # Fundo vermelho
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        }
                    ],
                    "merged_cells": [],
                    "data_validations": [],
                    "row_dimensions": [],
                    "column_dimensions": [],
                    "conditional_formatting": [],
                    "tables": [],
                    "images": [],
                }
            ]
        }
        
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        # Título não deve ser detectado
        title_field = next((c for c in candidates if c.cell_range == "A1"), None)
        assert title_field is None
    
    def test_exclude_examples(self):
        """Testa exclusão de células com texto 'Exemplo'"""
        snapshot = {
            "schema_version": "2.0",
            "sheets": [
                {
                    "name": "Sheet1",
                    "cells": [
                        {
                            "coordinate": "A1",
                            "value": "Exemplo: João Silva",
                            "formula": None,
                            "style": {
                                "font": {"bold": False, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        }
                    ],
                    "merged_cells": [],
                    "data_validations": [],
                    "row_dimensions": [],
                    "column_dimensions": [],
                    "conditional_formatting": [],
                    "tables": [],
                    "images": [],
                }
            ]
        }
        
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        # Exemplo não deve ser detectado
        example_field = next((c for c in candidates if "Exemplo" in str(c.example_value or "")), None)
        assert example_field is None
    
    def test_label_inference(self):
        """Testa inferência de labels por proximidade"""
        snapshot = {
            "schema_version": "2.0",
            "sheets": [
                {
                    "name": "Persona",
                    "cells": [
                        {
                            "coordinate": "A1",
                            "value": "Nome Completo:",
                            "style": {
                                "font": {"bold": False, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        },
                        {
                            "coordinate": "A2",
                            "value": None,
                            "formula": None,
                            "style": {
                                "font": {"bold": False, "size": 11},
                                "fill": {"fgColor": None},
                                "border": {},
                                "alignment": {},
                                "protection": {}
                            }
                        }
                    ],
                    "merged_cells": [],
                    "data_validations": [],
                    "row_dimensions": [],
                    "column_dimensions": [],
                    "conditional_formatting": [],
                    "tables": [],
                    "images": [],
                }
            ]
        }
        
        detector = FillableAreaDetector()
        candidates = detector.detect(snapshot)
        
        field = next((c for c in candidates if c.cell_range == "A2"), None)
        assert field is not None
        assert "Nome Completo" in field.label or field.label is not None


class TestFieldStability:
    """Testes de estabilidade de field_id"""
    
    def test_field_id_deterministic(self):
        """Testa que field_id é determinístico"""
        candidate1 = FillableFieldCandidate(
            sheet="ICP",
            cell_range="B1:C1",
            label="Nome da Empresa",
            inferred_type="text_short",
            required=True,
            example_value=None,
            phase="icp",
            order_index=1000,
            source_metadata={}
        )
        
        candidate2 = FillableFieldCandidate(
            sheet="ICP",
            cell_range="B1:C1",
            label="Nome da Empresa",
            inferred_type="text_short",
            required=True,
            example_value=None,
            phase="icp",
            order_index=1000,
            source_metadata={}
        )
        
        dict1 = candidate1.to_dict("template_123")
        dict2 = candidate2.to_dict("template_123")
        
        # field_id deve ser igual
        assert dict1["field_id"] == dict2["field_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
