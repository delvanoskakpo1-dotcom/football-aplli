from flask import Flask, request, jsonify
import math

app = Flask(__name__)

# Clé API sécurisée
API_KEY = "SUPER_SECRET_KEY_123"

# Fonction Poisson
def poisson(lmbda, k):
    return (lmbda**k * math.exp(-lmbda)) / math.factorial(k)

@app.route("/predict", methods=["POST"])
def predict():
    key = request.headers.get("X-API-KEY")
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    home = data.get("home")
    away = data.get("away")
    odds_1x2 = data.get("odds_1x2")
    odds_over_under = data.get("odds_over_under")

    # Vérification basique
    if not home or not away or not odds_1x2:
        return jsonify({"error": "Missing required fields"}), 400

    # Convertir les cotes en probabilités implicites (enlever la marge simple)
    def prob_from_odds(odds):
        total = sum(1/o for o in odds)
        return [(1/o)/total*100 for o in odds]

    prob_H, prob_D, prob_A = prob_from_odds([odds_1x2["H"], odds_1x2["D"], odds_1x2["A"]])

    # Calcul lambda pour Poisson (simplifié)
    lambda_home = prob_H/100 * 3  # 3 est un coefficient ajustable
    lambda_away = prob_A/100 * 3

    # Top scores exacts (0-3)
    top_scores = {}
    for i in range(4):
        for j in range(4):
            p = poisson(lambda_home, i) * poisson(lambda_away, j) * 100
            top_scores[f"{i}-{j}"] = round(p, 2)

    # Trier top 5
    top_scores_sorted = dict(sorted(top_scores.items(), key=lambda x: x[1], reverse=True)[:5])

    # BTTS
    btts = 1 - (poisson(lambda_home, 0) * poisson(lambda_away, 0))
    btts = round(btts*100, 2)

    # Over 2.5
    total_goals_prob = 0
    for i in range(4):
        for j in range(4):
            if i+j > 2:
                total_goals_prob += poisson(lambda_home, i)*poisson(lambda_away, j)
    over_2_5 = round(total_goals_prob*100, 2)

    # Résultat final
    result = {
        "match": f"{home} vs {away}",
        "expected_goals": {"home": round(lambda_home,2), "away": round(lambda_away,2)},
        "top_exact_scores (%)": top_scores_sorted,
        "BTTS (%)": btts,
        "Over_2.5 (%)": over_2_5,
        "ML_1X2_probabilities (%)": {"Home": round(prob_H,2), "Draw": round(prob_D,2), "Away": round(prob_A,2)}
    }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)