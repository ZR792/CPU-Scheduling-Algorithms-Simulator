import matplotlib.pyplot as plt
from typing import List, Tuple
from pathlib import Path


# Renders a static Gantt image from a gantt list
# gantt: List[Tuple[pid, start, duration]]


def render_gantt_image(gantt: List[Tuple[str, int, int]], filename: str = 'examples/gantt.png') -> str:
    """
    Render a Gantt chart image from gantt data and save it to `filename`.

    Args:
        gantt: list of tuples (pid, start, duration)
        filename: path to save the image

    Returns:
        the filename that was saved

    Raises:
        ValueError if gantt is empty
        Any exception raised by matplotlib/file IO will propagate.
    """
    if not gantt:
        raise ValueError('Empty gantt data')

    # Ensure output directory exists
    out_path = Path(filename)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine unique pids and assign rows
    pids = sorted(list({pid for pid, _, _ in gantt}))
    pid_index = {pid: idx for idx, pid in enumerate(pids)}

    fig_height = max(2.5, 0.6 * len(pids))
    fig, ax = plt.subplots(figsize=(10, fig_height))

    for pid, start, dur in gantt:
        y = pid_index[pid]
        ax.barh(y, dur, left=start, height=0.6)
        # place the pid label centered in the bar (if the bar is too small, it may overlap)
        ax.text(start + dur / 2, y, pid, va='center', ha='center', color='white', fontsize=9)

    ax.set_yticks(list(range(len(pids))))
    ax.set_yticklabels(pids)
    ax.set_xlabel('Time')
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(str(out_path))
    plt.close(fig)
    return str(out_path)
