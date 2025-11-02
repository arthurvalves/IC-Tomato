from collections import defaultdict
from typing import Dict, Set, Tuple, Optional, List
import json

EPSILON = "&"

class MaquinaMealy:
    """Representa uma Máquina de Mealy."""
    def __init__(self):
        self.states: Set[str] = set()
        self.start_state: Optional[str] = None
        self.input_alphabet: Set[str] = set()
        self.output_alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[str, str], Tuple[str, str]] = {}

    def add_state(self, state: str, is_start: bool = False):
        """Adiciona um novo estado à máquina."""
        self.states.add(state)
        if is_start or self.start_state is None:
            self.start_state = state

    def add_transition(self, src: str, input_symbol: str, dst: str, output_symbol: str):
        """Adiciona uma transição à máquina."""
        if src not in self.states or dst not in self.states:
            raise ValueError(f"Estado de origem '{src}' ou destino '{dst}' não existe.")
        
        self.input_alphabet.add(input_symbol)
        self.output_alphabet.add(output_symbol)
        self.transitions[(src, input_symbol)] = (dst, output_symbol)

    def remove_state(self, state_to_remove: str):
        """Remove um estado e todas as suas transições associadas."""
        if state_to_remove not in self.states:
            return

        self.states.discard(state_to_remove)

        if self.start_state == state_to_remove:
            self.start_state = None

        new_transitions = {}
        for (src, in_sym), (dst, out_sym) in self.transitions.items():
            if src != state_to_remove and dst != state_to_remove:
                new_transitions[(src, in_sym)] = (dst, out_sym)
        self.transitions = new_transitions

    def remove_transition(self, src: str, input_symbol: str):
        """Remove uma transição específica baseada na origem e no símbolo de entrada."""
        key = (src, input_symbol)
        if key in self.transitions:
            del self.transitions[key]

    def rename_state(self, old_name: str, new_name: str):
        """Renomeia um estado em toda a estrutura da máquina."""
        if old_name not in self.states:
            raise ValueError(f"Estado '{old_name}' não existe.")
        if new_name in self.states and new_name != old_name:
            raise ValueError(f"O nome '{new_name}' já está em uso.")

        self.states.remove(old_name)
        self.states.add(new_name)

        if self.start_state == old_name:
            self.start_state = new_name

        new_transitions = {}
        for (src, in_sym), (dst, out_sym) in self.transitions.items():
            new_src = new_name if src == old_name else src
            new_dst = new_name if dst == old_name else dst
            new_transitions[(new_src, in_sym)] = (new_dst, out_sym)
        self.transitions = new_transitions

    def simulate(self, input_str: str) -> Optional[str]:
        """Simulação rápida que retorna apenas a saída final."""
        _, final_output = self.simulate_history(input_str)
        return final_output

    def simulate_history(self, input_str: str) -> Tuple[List[Tuple[str, str, int]], Optional[str]]:
        """
        Simula a execução e retorna o histórico de passos para animação.
        Modificado para suportar transições com múltiplos caracteres (ex: "aa").
        
        Retorna uma tupla contendo (histórico, saída_final).
        O histórico é uma lista de tuplas (estado_atual, saida_acumulada, input_idx_consumido).
        Retorna None como saída_final se a máquina travar.
        """
        if not self.start_state:
            return [], None

        current_state = self.start_state
        output_str = ""
        input_idx = 0
        history = [(current_state, "", 0)]

        while input_idx < len(input_str):
            possible_symbols = set()
            for (src, sym) in self.transitions.keys():
                if src == current_state:
                    possible_symbols.add(sym)

            sorted_symbols = sorted(list(possible_symbols), key=len, reverse=True)

            remaining_input = input_str[input_idx:]
            consumed = False

            for symbol in sorted_symbols:
                if remaining_input.startswith(symbol):
                    next_state, output_symbol = self.transitions[(current_state, symbol)]
                    
                    output_str += output_symbol
                    current_state = next_state
                    input_idx += len(symbol)
                    
                    history.append((current_state, output_str, input_idx))
                    consumed = True
                    break

            if not consumed:
                return history, None
        
        return history, output_str


    def to_json(self) -> str:
        """Serializa a máquina para uma string JSON."""
        data = {
            "states": list(self.states),
            "start_state": self.start_state,
            "input_alphabet": list(self.input_alphabet),
            "output_alphabet": list(self.output_alphabet),
            "transitions": [
                {"src": src, "input": in_sym, "dst": dst, "output": out_sym}
                for (src, in_sym), (dst, out_sym) in self.transitions.items()
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'MaquinaMealy':
        """Cria uma Máquina de Mealy a partir de uma string JSON."""
        data = json.loads(json_str)
        machine = cls()
        
        for s in data.get("states", []):
            machine.add_state(s, is_start=(s == data.get("start_state")))
        
        for t in data.get("transitions", []):
            machine.add_transition(t["src"], t["input"], t["dst"], t["output"])
            
        return machine