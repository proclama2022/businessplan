#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pacchetto per la gestione del chunking di documenti lunghi

Questo pacchetto contiene moduli per suddividere documenti lunghi in chunk gestibili,
utilizzando diverse strategie di chunking per mantenere il contesto e la struttura.
"""

from .hierarchical import (
    detect_section_structure,
    chunk_document,
    generate_chunk_summaries,
    merge_chunks,
    count_tokens
)