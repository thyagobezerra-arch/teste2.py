import requests
from scipy.stats import poisson

API_KEY = "SUA_API_KEY_AQUI"
HEADERS = {'x-rapidapi-key': API_KEY}

def get_team_scoring_avg(team_id, league_id, season=2025):
    url = "https://v3.football.api-sports.io/teams/statistics"
    params = {"league": league_id, "team": team_id, "season": season}
    
    response = requests.get(url, headers=HEADERS, params=params).json()
    
    # Pegamos a média de gols marcados e sofridos
    goals_for = response['response']['goals']['for']['average']['total']
    goals_against = response['response']['goals']['against']['average']['total']
    
    return float(goals_for), float(goals_against)

def calcular_edge(home_id, away_id, league_id, odd_casa):
    # 1. Busca médias reais na API
    home_attack, _ = get_team_scoring_avg(home_id, league_id)
    _, away_defense = get_team_scoring_avg(away_id, league_id)
    
    # 2. Motor de Poisson (Média projetada de gols no jogo)
    lambda_jogo = (home_attack + away_defense) / 2 # Simplificação do modelo
    
    # Probabilidade de sair 0, 1 ou 2 gols (Under 2.5)
    prob_under = sum([poisson.pmf(i, lambda_jogo) for i in range(3)])
    prob_over = (1 - prob_under) * 100
    
    # 3. Cálculo da Vantagem (Edge)
    odd_justa = 100 / prob_over
    edge = (odd_casa / odd_justa) - 1
    
    return round(prob_over, 2), round(odd_justa, 2), round(edge * 100, 2)

# EXEMPLO: Manchester City (50) vs Liverpool (40) na Premier League (39)
# Imagine que a Bet365 está pagando 2.10 para o Over 2.5
prob, justa, vantagem = calcular_edge(50, 40, 39, 2.10)

print(f"📈 Probabilidade Over 2.5: {prob}%")
print(f"💎 Odd Justa: {justa}")
print(f"💰 Vantagem (Edge): {vantagem}%")