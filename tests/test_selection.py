"""목록 선택 상태 토글 — fragment 제거 후 회귀 방지."""
from __future__ import annotations


class _State(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def _toggle_select(state: _State, idx: int) -> None:
    """app.toggle_select 와 동일 로직 (Streamlit 없이 검증)."""
    sel: list = list(state.get("selected", []))
    if idx in sel:
        sel.remove(idx)
    elif len(sel) < 2:
        sel.append(idx)
    else:
        sel[1] = idx
    state["selected"] = sel


def test_select_one():
    s = _State(selected=[])
    _toggle_select(s, 3)
    assert s["selected"] == [3]


def test_select_two():
    s = _State(selected=[3])
    _toggle_select(s, 5)
    assert s["selected"] == [3, 5]


def test_replace_second_slot():
    s = _State(selected=[3, 5])
    _toggle_select(s, 7)
    assert s["selected"] == [3, 7]


def test_deselect():
    s = _State(selected=[3, 5])
    _toggle_select(s, 3)
    assert s["selected"] == [5]
