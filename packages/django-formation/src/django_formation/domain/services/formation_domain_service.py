

class FormationDomainService:
    @staticmethod
    def verifier_meme_etablissement(*args) -> bool:
        if len(args) < 2:
            return True
        first = args[0]
        return all(getattr(a, "etablissement_id", None) == getattr(first, "etablissement_id", None) for a in args[1:])
