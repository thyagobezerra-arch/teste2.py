from scipy.stats import poisson

def calcular_probabilidade_over25(media_time_a, media_time_b):
    media_total = media_time_a + media_time_b
    
    # Calculamos a chance de sair 0, 1 e 2 gols
    prob_0 = poisson.pmf(0, media_total)
    prob_1 = poisson.pmf(1, media_total)
    prob_2 = poisson.pmf(2, media_total)
    
    # A probabilidade de Under 2.5 é a soma de 0, 1 e 2 gols
    prob_under_25 = prob_0 + prob_1 + prob_2
    
    # A probabilidade de Over 2.5 é 100% menos o Under
    prob_over_25 = 1 - prob_under_25
    
    return round(prob_over_25 * 100, 2)

# TESTE REAL
media_a = 2.1  # Ex: Média do Flamengo em casa
media_b = 1.4  # Ex: Média do Palmeiras fora
chance = calcular_probabilidade_over25(media_a, media_b)

print(f"📊 Análise: {media_a} vs {media_b}")
print(f"📈 Probabilidade de +2.5 Gols: {chance}%")

# Calculando a ODD JUSTA
odd_justa = round(100 / chance, 2) if chance > 0 else 0
print(f"💎 Odd Justa (Preço que vale a pena): {odd_justa}")