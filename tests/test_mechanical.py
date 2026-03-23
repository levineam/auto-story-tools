"""Tests for the mechanical slop detector."""

from auto_outline.evaluation.mechanical import slop_score


class TestTier1Detection:
    """Tier 1 banned words should always be caught."""

    def test_catches_delve(self):
        result = slop_score("Let us delve into the mystery of the ancient forest.")
        assert any(w == "delve" for w, _ in result["tier1_hits"])

    def test_catches_utilize(self):
        result = slop_score("She decided to utilize the artifact's power.")
        assert any(w == "utilize" for w, _ in result["tier1_hits"])

    def test_catches_multifaceted(self):
        result = slop_score("The multifaceted problem required a new approach.")
        assert any(w == "multifaceted" for w, _ in result["tier1_hits"])

    def test_clean_text_no_tier1(self):
        result = slop_score("The old man walked to the river and sat down.")
        assert len(result["tier1_hits"]) == 0


class TestTier2Clusters:
    """Tier 2 words should flag when clustered."""

    def test_single_tier2_no_penalty(self):
        result = slop_score("The system was robust enough to handle the load.")
        # Single occurrence = no cluster penalty
        assert result["tier2_clusters"] == 0

    def test_cluster_detected(self):
        text = (
            "This robust and comprehensive approach provides a seamless "
            "experience that fosters innovation."
        )
        result = slop_score(text)
        assert result["tier2_clusters"] >= 1


class TestTier3Filler:
    """Tier 3 filler phrases should be caught."""

    def test_catches_worth_noting(self):
        result = slop_score("It's worth noting that the river flows north.")
        assert len(result["tier3_hits"]) > 0

    def test_catches_lets_dive(self):
        result = slop_score("Let's dive into the backstory of this character.")
        assert len(result["tier3_hits"]) > 0

    def test_clean_prose_no_filler(self):
        result = slop_score("The river flows north. It always has.")
        assert len(result["tier3_hits"]) == 0


class TestSlopPenalty:
    """Overall penalty score should scale with slop density."""

    def test_clean_prose_low_penalty(self):
        text = (
            "Rain fell on the tin roof. The sound was steady, almost musical. "
            "She sat by the window and watched the drops slide down the glass. "
            "Nothing moved outside. The street was empty."
        )
        result = slop_score(text)
        assert result["slop_penalty"] <= 2.0

    def test_sloppy_text_high_penalty(self):
        text = (
            "It's worth noting that this multifaceted tapestry of endeavors "
            "leverages a holistic paradigm to facilitate synergy. Furthermore, "
            "the comprehensive approach utilizes cutting-edge innovation to "
            "catalyze a seamless transformation. Additionally, this robust "
            "cornerstone fosters empowerment."
        )
        result = slop_score(text)
        assert result["slop_penalty"] >= 5.0


class TestEmDashDensity:
    """Em dash density should be measured."""

    def test_em_dash_counted(self):
        text = "He ran — fast — toward the light — and stopped."
        result = slop_score(text)
        assert result["em_dash_density"] > 0

    def test_no_em_dash(self):
        text = "He ran fast toward the light and stopped."
        result = slop_score(text)
        assert result["em_dash_density"] == 0


class TestSentenceLengthVariation:
    """Sentence length CV should reflect variation."""

    def test_varied_sentences(self):
        text = (
            "Stop. The old cathedral stood at the edge of town, its spire "
            "reaching toward clouds that never seemed to move, a permanent "
            "fixture against the grey sky that had defined this place for "
            "three hundred years. Rain. She walked inside."
        )
        result = slop_score(text)
        assert result["sentence_length_cv"] > 0.3

    def test_uniform_sentences(self):
        text = (
            "The man walked to the store. The woman drove to the park. "
            "The child ran to the school. The dog went to the yard. "
            "The cat sat on the mat."
        )
        result = slop_score(text)
        assert result["sentence_length_cv"] < 0.5
