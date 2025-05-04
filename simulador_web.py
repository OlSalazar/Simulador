import streamlit as st

# Configurações base
config = {
    "campo": {"rendimento": 200, "custo_m2": 0.0778},
    "floresta": {"rendimento": 190, "custo_m2": 0.09502},
}

st.set_page_config(page_title="Simulador de Terrenos", layout="centered")

st.markdown("## 🛠️ Simulador de Orçamento - Limpeza de Terrenos")
st.markdown("Calcular preço justo com base na área, altura da vegetação e equipa.")
st.markdown("---")

# Inputs
tipo = st.selectbox("Tipo de corte:", ["campo", "floresta"])
area = st.number_input("Área do terreno (m²):", min_value=0.0, step=10.0, format="%.1f")
altura = st.number_input("Altura da vegetação (cm):", min_value=0.0, step=0.1, format="%.1f")
trabalhadores = st.number_input("Nº de trabalhadores:", min_value=1, step=1)
margem = st.slider("Margem de lucro (%):", 0, 100, 25)

if st.button("Calcular orçamento"):
    dados = config[tipo]
    rendimento = dados["rendimento"]
    custo_m2 = dados["custo_m2"]

    # Fator de sujidade (conforme altura)
    if altura <= 0.4:
        fator_sujidade = 0.95
    elif altura <= 1:
        fator_sujidade = 1
    elif altura <= 1.5:
        fator_sujidade = 1.1
    elif altura <= 2:
        fator_sujidade = 1.2
    elif altura <= 2.5:
        fator_sujidade = 1.3
    else:
        fator_sujidade = 1.5

    rendimento_total = rendimento * trabalhadores / fator_sujidade
    tempo_estimado = area / rendimento_total

    custo_total = area * custo_m2
    preco_final = custo_total * (1 + margem / 100)

    st.markdown("### 📊 Resultado")
    st.success(f"⏱️ Tempo estimado: **{tempo_estimado:.2f} horas**")
    st.success(f"💰 Preço final sugerido: **{preco_final:.2f} €**")

    st.markdown("---")
    st.info("Este simulador é uma ferramenta indicativa. Adapta conforme o terreno real.")
