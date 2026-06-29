class AdaptiveEngine:

    @staticmethod
    def get_next_difficulty(
        level: str,
        current_difficulty: int
    ) -> tuple[int, str]:

        if level == "strong":
            return min(current_difficulty + 1, 5), "harder"

        elif level == "weak":
            return max(current_difficulty - 1, 1), "easier"

        return current_difficulty, "same"