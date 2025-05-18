import streamlit as st
import json
import os

# Carrega o config.json
CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
    st.error("❌ Ficheiro config.json não encontrado.")
    st.stop()

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

# Interface
st.set_page_config(page_title="Simulador de Terrenos", layout="centered")
st.title("📊 Simulador de Limpeza de Terrenos")
st.markdown("Preenche os dados abaixo para obter uma estimativa:")

# Entradas
tipo = st.selectbox("🪓 Tipo de corte:", ["Campo", "Floresta"]).lower()
area = st.number_input("🧱 Área do terreno (m²):", min_value=0.0, step=10.0)
altura_cm = st.number_input("🌿 Altura da vegetação (cm):", min_value=0.0, step=1.0)
trabalhadores = st.number_input("👷 Nº de trabalhadores:", min_value=1, step=1)
margem = st.slider("📈 Margem de lucro (%):", min_value=0, max_value=100, value=25)

if st.button("Calcular orçamento"):
    try:
        rendimento = config[tipo]["rendimento"]

        # Custo base €/m² conforme tipo e nº de trabalhadores
        custos_base = {
            "campo": {1: 0.0667, 2: 0.1334},
            "floresta": {1: 0.08491, 2: 0.16982}
        }
        custo_m2_base = custos_base[tipo][1 if trabalhadores == 1 else 2]

        # Fator vegetação
        fator_vegetacao = 1 + (max(0, int((altura_cm - 30) / 10)) * 0.10)

        # Cálculos
        preco_com_iva = custo_m2_base * fator_vegetacao * area * 1.06
        preco_final = preco_com_iva * (1 + margem / 100)
        tempo_horas = (area / rendimento) * fator_vegetacao / trabalhadores

        # Resultados
        st.markdown("### 📊 Resultado")
        st.success(f"⏱ Tempo estimado: **{tempo_horas:.1f} horas**")
        st.success(f"💶 Preço Total com IVA: **{preco_com_iva:.2f} €**")
        st.warning(f"💸 Preço Venda Total: **{preco_final:.2f} €**")

        st.info("Este valor inclui fator de dificuldade pela altura da vegetação.")
    except Exception as e:
        st.error(f"Erro: {str(e)}")
