import json
from collections import defaultdict
from typing import Dict, Set, Tuple, Optional, List

BLANK_SYMBOL = "β" 
DEFAULT_MAX_STEPS = 1000

class MaquinaTuring:
    """
    Representa uma Máquina de Turing determinística padrão.
    """
    def __init__(self):
        self.states: Set[str] = set()
        self.start_state: Optional[str] = None
        self.final_states: Set[str] = set()
        self.input_alphabet: Set[str] = set()
        self.tape_alphabet: Set[str] = {BLANK_SYMBOL}
        self.blank_symbol: str = BLANK_SYMBOL
        
        self.transitions: Dict[Tuple[str, str], Tuple[str, str, str]] = {}

    def add_state(self, state: str, is_start: bool = False, is_final: bool = False):
        """Adiciona um novo estado à máquina."""
        self.states.add(state)
        if is_start or (self.start_state is None and not self.states):
            self.start_state = state
        if is_final:
            self.final_states.add(state)

    def add_transition(self, src: str, read: str, dst: str, write: str, direction: str):
        """
        Adiciona uma transição determinística.
        (src, read) -> (dst, write, direction)
        """
        if src not in self.states or dst not in self.states:
            raise ValueError("Estado de origem ou destino inválido.")
        if direction not in {'L', 'R'}:
            raise ValueError("Direção deve ser 'L' ou 'R'.")
        
        self.input_alphabet.add(read)
        self.tape_alphabet.add(read)
        self.tape_alphabet.add(write)

        self.transitions[(src, read)] = (dst, write, direction)

    def remove_state(self, state_to_remove: str):
        """Remove um estado e todas as suas transições associadas."""
        if state_to_remove not in self.states:
            return

        self.states.discard(state_to_remove)

        if self.start_state == state_to_remove:
            self.start_state = None

        self.final_states.discard(state_to_remove)

        new_transitions = {}
        for (src, read), (dst, write, move) in self.transitions.items():
            if src != state_to_remove and dst != state_to_remove:
                new_transitions[(src, read)] = (dst, write, move)
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
        
        if old_name in self.final_states:
            self.final_states.remove(old_name)
            self.final_states.add(new_name)

        new_transitions = {}
        for (src, read), (dst, write, move) in self.transitions.items():
            new_src = new_name if src == old_name else src
            new_dst = new_name if dst == old_name else dst
            new_transitions[(new_src, read)] = (new_dst, write, move)
        self.transitions = new_transitions

    def simulate_history(self, input_str: str, max_steps=DEFAULT_MAX_STEPS) -> Tuple[List[Tuple[str, Dict[int, str], int]], str]:
        """
        Simula a execução da Máquina de Turing e retorna o histórico de configurações.
        
        Retorna:
            - Uma lista de (estado, fita_como_dict, pos_cabeca)
            - Uma string de resultado: "ACEITO", "REJEITADO", ou "LOOP"
        """
        if not self.start_state:
            return [], "REJEITADO"

        tape = defaultdict(lambda: self.blank_symbol)
        for i, symbol in enumerate(input_str):
            tape[i] = symbol
            
        current_state = self.start_state
        head_pos = 0
        step_count = 0

        history: List[Tuple[str, Dict[int, str], int]] = [(current_state, dict(tape), head_pos)]

        while step_count < max_steps:
            if current_state in self.final_states:
                return history, "ACEITO"
            
            read_symbol = tape[head_pos]
            transition_key = (current_state, read_symbol)

            if transition_key not in self.transitions:
                return history, "REJEITADO"

            (next_state, write_symbol, direction) = self.transitions[transition_key]
            
            tape[head_pos] = write_symbol
            
            if direction == 'R':
                head_pos += 1
            else: 
                head_pos -= 1
                
            current_state = next_state
            step_count += 1
            
            history.append((current_state, dict(tape), head_pos))

        return history, "LOOP"

    def simulate(self, input_str: str) -> bool:
        """Simulação rápida que retorna apenas se foi aceito ou não."""
        _, result = self.simulate_history(input_str)
        return result == "ACEITO"

    def to_json(self) -> str:
        """Serializa a máquina para uma string JSON."""
        serializable_transitions = {}
        for (src, read), (dst, write, move) in self.transitions.items():
            key = f"{src},{read}"
            value = (dst, write, move)
            serializable_transitions[key] = value
            
        data = {
            "states": list(self.states),
            "start_state": self.start_state,
            "final_states": list(self.final_states),
            "input_alphabet": list(self.input_alphabet),
            "tape_alphabet": list(self.tape_alphabet),
            "blank_symbol": self.blank_symbol,
            "transitions": serializable_transitions
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'MaquinaTuring':
        """Cria uma Máquina de Turing a partir de uma string JSON."""
        data = json.loads(json_str)
        tm = cls()
        
        tm.states = set(data.get("states", []))
        tm.start_state = data.get("start_state")
        tm.final_states = set(data.get("final_states", []))
        tm.input_alphabet = set(data.get("input_alphabet", []))
        tm.blank_symbol = data.get("blank_symbol", BLANK_SYMBOL)
        tm.tape_alphabet = set(data.get("tape_alphabet", [tm.blank_symbol]))
        
        for key, value in data.get("transitions", {}).items():
            try:
                src, read = key.split(',', 1)
                dst, write, move = value
                tm.add_transition(src, read, dst, write, move)
            except (ValueError, TypeError):
                print(f"Aviso: Ignorando transição malformada: {key} -> {value}")
                
        return tm
        

def snapshot_of_turing(machine: MaquinaTuring, positions: Dict[str, Tuple[int, int]]) -> str:
    """Retorna JSON serializável representando o estado completo (máquina + posições)."""
    data = {
        "turing_machine": json.loads(machine.to_json()),
        "positions": positions
    }
    return json.dumps(data, ensure_ascii=False)

def restore_from_turing_snapshot(s: str) -> Tuple[MaquinaTuring, Dict[str, Tuple[int, int]]]:
    """Restaura uma máquina de Turing e suas posições a partir de um snapshot JSON."""
    data = json.loads(s)
    
    machine_data = data.get("turing_machine", {})
    if isinstance(machine_data, str):
        machine_data = json.loads(machine_data)

    machine = MaquinaTuring.from_json(json.dumps(machine_data))
    positions = data.get("positions", {})
    return machine, positions