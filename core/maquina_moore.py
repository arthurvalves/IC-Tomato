from collections import defaultdict
from typing import Dict, Set, Tuple, Optional, List
import json

EPSILON = "&"

class MaquinaMoore:
    """Representa uma Máquina de Moore."""
    def __init__(self):
        self.states: Set[str] = set()
        self.start_state: Optional[str] = None
        self.input_alphabet: Set[str] = set()
        self.output_alphabet: Set[str] = set()
        self.output_function: Dict[str, str] = {}
        self.transitions: Dict[Tuple[str, str], str] = {}

    def add_state(self, state: str, output_symbol: str, is_start: bool = False):
        """Adiciona um novo estado com seu símbolo de saída."""
        self.states.add(state)
        self.output_function[state] = output_symbol
        self.output_alphabet.add(output_symbol)
        if is_start or self.start_state is None:
            self.start_state = state

    def add_transition(self, src: str, input_symbol: str, dst: str):
        """Adiciona uma transição à máquina."""
        if src not in self.states or dst not in self.states:
            raise ValueError(f"Estado de origem '{src}' ou destino '{dst}' não existe.")
        
        self.input_alphabet.add(input_symbol)
        self.transitions[(src, input_symbol)] = dst

    def remove_state(self, state_to_remove: str):
        """Remove um estado e todas as suas transições associadas."""
        if state_to_remove not in self.states:
            return

        self.states.discard(state_to_remove)
        if state_to_remove in self.output_function:
            del self.output_function[state_to_remove]

        if self.start_state == state_to_remove:
            self.start_state = None

        new_transitions = {}
        for (src, in_sym), dst in self.transitions.items():
            if src != state_to_remove and dst != state_to_remove:
                new_transitions[(src, in_sym)] = dst
        self.transitions = new_transitions

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

        self.output_function[new_name] = self.output_function.pop(old_name)

        new_transitions = {}
        for (src, in_sym), dst in self.transitions.items():
            new_src = new_name if src == old_name else src
            new_dst = new_name if dst == old_name else dst
            new_transitions[(new_src, in_sym)] = new_dst
        self.transitions = new_transitions
        
    def remove_transition(self, src: str, input_symbol: str):
        """Remove uma transição específica baseada na origem e no símbolo de entrada."""
        key = (src, input_symbol)
        if key in self.transitions:
            del self.transitions[key]

    def simulate_history(self, input_str: str) -> Tuple[List[Tuple[str, str, int]], Optional[str]]:
        """
        Simula a execução e retorna o histórico de passos.
        Modificado para suportar transições com múltiplos caracteres (ex: "aa").
        A saída de Moore é baseada no estado, então a saída inicial é a do estado inicial.
        
        Retorna:
            - history: Lista de (estado_atual, saida_acumulada, input_idx_consumido)
            - final_output: String da saída completa ou None se travar.
        """
        if not self.start_state:
            return [], None

        current_state = self.start_state
        output_str = self.output_function.get(current_state, '') 
        input_idx = 0
        
        history = [(current_state, output_str, 0)]

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
                    next_state = self.transitions[(current_state, symbol)]
                    
                    output_str += self.output_function.get(next_state, '') 
                    
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
        input_alpha = list(filter(None, self.input_alphabet))
        output_alpha = list(filter(None, self.output_alphabet))
        
        data = {
            "states": list(self.states),
            "start_state": self.start_state,
            "input_alphabet": input_alpha,
            "output_alphabet": output_alpha,
            "output_function": self.output_function,
            "transitions": [
                {"src": src, "input": in_sym, "dst": dst}
                for (src, in_sym), dst in self.transitions.items()
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'MaquinaMoore':
        """Cria uma Máquina de Moore a partir de uma string JSON."""
        data = json.loads(json_str)
        machine = cls()
        
        output_func = data.get("output_function", {})
        for state, output in output_func.items():
            machine.add_state(state, output, is_start=(state == data.get("start_state")))
        
        machine.input_alphabet = set()
        machine.output_alphabet = set(output_func.values())

        for t in data.get("transitions", []):
            try:
                machine.add_transition(t["src"], t["input"], t["dst"])
            except KeyError as e:
                print(f"Aviso: Ignorando transição malformada (chave faltando: {e}): {t}")
            except ValueError as e:
                 print(f"Aviso: Ignorando transição inválida ({e}): {t}")

        if machine.start_state not in machine.states:
            if machine.states:
                machine.start_state = next(iter(machine.states))
                print(f"Aviso: Estado inicial '{data.get('start_state')}' não encontrado. Definindo '{machine.start_state}' como inicial.")
            else:
                 machine.start_state = None


        return machine

def snapshot_of_moore(machine: MaquinaMoore, positions: Dict[str, Tuple[int, int]]) -> str:
    """Retorna JSON serializável representando o estado completo (máquina + posições)."""
    data = {
        "moore_machine": json.loads(machine.to_json()),
        "positions": positions
    }
    return json.dumps(data, ensure_ascii=False)

def restore_from_moore_snapshot(s: str) -> Tuple[MaquinaMoore, Dict[str, Tuple[int, int]]]:
    """Restaura uma máquina de Moore e suas posições a partir de um snapshot JSON."""
    data = json.loads(s)
    
    machine_data = data.get("moore_machine", {})
    if isinstance(machine_data, str):
        machine_data = json.loads(machine_data)

    machine = MaquinaMoore.from_json(json.dumps(machine_data))
    positions = data.get("positions", {})
    return machine, positions