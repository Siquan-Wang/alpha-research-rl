"""Chronological, label-purged research intervals (all bounds half-open)."""

from dataclasses import dataclass
from numbers import Integral


@dataclass(frozen=True)
class ResearchSplit:
    fit: tuple[int, int]
    feedback: tuple[int, int]
    assessment: tuple[int, int]
    horizon: int = 5

    def __post_init__(self):
        if isinstance(self.horizon, bool) or not isinstance(self.horizon, Integral) or self.horizon < 1:
            raise ValueError("horizon must be a positive integer")
        object.__setattr__(self, "horizon", int(self.horizon))
        for name in ("fit", "feedback", "assessment"):
            bounds = getattr(self, name)
            if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
                raise ValueError("intervals must be pairs of integer bounds")
            if any(isinstance(x, bool) or not isinstance(x, Integral) for x in bounds):
                raise ValueError("interval bounds must be integers")
            start, stop = map(int, bounds)
            if start < 0 or stop <= start:
                raise ValueError("intervals must be nonempty and nonnegative")
            object.__setattr__(self, name, (start, stop))
        if self.fit[1] + self.horizon > self.feedback[0]:
            raise ValueError("fit labels overlap feedback; purge the horizon")
        if self.feedback[1] + self.horizon > self.assessment[0]:
            raise ValueError("feedback labels overlap assessment; purge the horizon")

    def validate_for_panel(self, n_dates: int) -> None:
        if self.assessment[1] + self.horizon > n_dates:
            raise ValueError("assessment labels extend beyond the panel")

    def to_dict(self) -> dict:
        """A manifest representation; deliberately absent from agent observations."""
        return {"fit": list(self.fit), "feedback": list(self.feedback),
                "assessment": list(self.assessment), "horizon": self.horizon}


def make_chronological_split(n_dates: int, horizon: int = 5,
                             fit_fraction: float = 0.4,
                             feedback_fraction: float = 0.3) -> ResearchSplit:
    """Split date blocks, removing boundary-crossing signal dates from each block."""
    if isinstance(n_dates, bool) or not isinstance(n_dates, Integral) or n_dates < 1:
        raise ValueError("n_dates must be a positive integer")
    if not (0 < fit_fraction < 1 and 0 < feedback_fraction < 1
            and fit_fraction + feedback_fraction < 1):
        raise ValueError("fractions must be positive and leave an assessment block")
    first = int(n_dates * fit_fraction)
    second = int(n_dates * (fit_fraction + feedback_fraction))
    split = ResearchSplit((0, first - horizon), (first, second - horizon),
                          (second, n_dates - horizon), horizon)
    split.validate_for_panel(n_dates)
    return split
