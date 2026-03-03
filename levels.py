from __future__ import annotations

from typing import Dict, List, Tuple

Node = Dict[str, object]
Edge = Tuple[int, int]

NODES: List[Node] = [
    {
        "id": 0,
        "pos": (130, 300),
        "quiz": {
            "question": "O que é uma rede neural artificial?",
            "options": [
                "Um banco de dados inteligente",
                "Um modelo computacional inspirado no cerebro humano",
                "Um tipo de linguagem de programacao",
                "Um algoritmo de ordenacao"
            ],
            "correct_index": 1,
        },
    },
    {
        "id": 1,
        "pos": (280, 330),
        "quiz": {
            "question": "Qual e a unidade basica de uma rede neural?",
            "options": [
                "Camada",
                "Gradiente",
                "Neuronio artificial",
                "Tensor"
            ],
            "correct_index": 2,
        },
    },
    {
        "id": 2,
        "pos": (420, 400),
        "quiz": {
            "question": "O que um neuronio artificial faz?",
            "options": [
                "Armazena dados permanentemente",
                "Soma entradas ponderadas e aplica uma funcao de ativacao",
                "Ordena numeros",
                "Executa loops"
            ],
            "correct_index": 1,
        },
    },
    {
        "id": 3,
        "pos": (430, 210),
        "quiz": {
            "question": "O que sao pesos (weights) em uma rede neural?",
            "options": [
                "Valores que definem a importancia das entradas",
                "Tipos de dados",
                "Camadas escondidas",
                "Funcoes matematicas fixas"
            ],
            "correct_index": 0,
        },
    },
    {
        "id": 4,
        "pos": (600, 390),
        "quiz": {
            "question": "O que e funcao de ativacao?",
            "options": [
                "Uma funcao que limpa os dados",
                "Um metodo para salvar o modelo",
                "Uma funcao que introduz nao-linearidade na rede",
                "Um tipo de banco de dados"
            ],
            "correct_index": 2,
        },
    },
    {
        "id": 5,
        "pos": (760, 300),
        "quiz": {
            "question": "O que e backpropagation?",
            "options": [
                "Um metodo de treinar a rede ajustando os pesos com base no erro",
                "Um tipo de banco de dados",
                "Uma linguagem de programacao",
                "Um algoritmo de busca"
            ],
            "correct_index": 0,
        },
    },
]

EDGES: List[Edge] = [
    (0, 1),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    (4, 5),
]


def build_neighbors(nodes: List[Node], edges: List[Edge]) -> Dict[int, List[int]]:
    neighbors: Dict[int, List[int]] = {int(node["id"]): [] for node in nodes}
    for a, b in edges:
        neighbors[a].append(b)
        neighbors[b].append(a)
    return neighbors


NEIGHBORS = build_neighbors(NODES, EDGES)
