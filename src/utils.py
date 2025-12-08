from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Process:
    pid: str
arrival: int
burst: int
priority: int
remaining: Optional[int] = None
start_time: Optional[int] = None
completion_time: Optional[int] = None
response_time: Optional[int] = None


def __post_init__(self):
    if self.remaining is None:
        self.remaining = self.burst




def compute_metrics(processes: List[Process]):
    n = len(processes)
    total_tat = sum((p.completion_time - p.arrival) for p in processes)
    total_wt = sum((p.completion_time - p.arrival - p.burst) for p in processes)
    total_rt = sum((p.response_time or 0) for p in processes)
    return {
'avg_tat': total_tat / n,
'avg_wt': total_wt / n,
'avg_rt': total_rt / n,
}
