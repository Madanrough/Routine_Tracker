"""Affectionate, deterministic daily messages without repetitive randomness."""

from __future__ import annotations

from datetime import date, datetime

MESSAGES = (
    "Chello, have a beautiful day.",
    "One good day at a time, Erumaaa.",
    "I'm proud of you for showing up today. ❤️",
    "Chello, consistency matters more than perfection.",
    "Small habits. Better days. One step at a time.",
    "You don't have to be perfect. Just keep showing up.",
    "A little care today can make tomorrow feel lighter.",
    "Alagiii, your steady effort matters. ❤️",
    "Take today gently, one small choice at a time.",
    "Your progress is made of ordinary days like this one.",
    "Chello, be proud of every honest effort.",
    "Today is another chance to care for yourself.",
    "Quiet consistency is still beautiful progress.",
    "Erumaaa, you are doing better than you think. ❤️",
    "Small steps still count, always.",
    "Make a little space for yourself today.",
    "Showing up is already worth celebrating.",
    "Paithiyo, keep going at your own pace. 😘",
    "A calm day and a kind heart are enough.",
    "Let today be simple, steady, and yours.",
    "Chello, every fresh day is a gentle reset.",
    "There is strength in taking care of the little things.",
    "Your effort deserves kindness, not pressure.",
    "Alagiii, one thoughtful choice at a time. ❤️",
    "Keep the promise you made to care for yourself.",
    "A good routine is built softly, day by day.",
    "You showed up—and that matters.",
    "Progress can be quiet and still be real.",
    "Chello, let consistency feel caring, not demanding.",
    "Today does not need to be perfect to be meaningful.",
    "Erumaaa, give yourself credit for beginning.",
    "Your small wins belong to you. ❤️",
    "Keep going, Alagiii. You're building something lovely.",
    "Kind choices add up.",
    "A fresh page, a gentle pace, a good day.",
    "Paithiyo, look at you choosing yourself today. 😘",
)


def greeting(now: datetime) -> str:
    if now.hour < 12:
        return "Good Morning, Erumaaa ❤️"
    if now.hour < 17:
        return "Good Afternoon, Paithiyo 😘"
    return "Good Evening, Alagiii ❤️"


def message_for_day(day: date) -> str:
    # 17 is coprime with the message count, so adjacent dates cannot repeat.
    return MESSAGES[(day.toordinal() * 17) % len(MESSAGES)]
