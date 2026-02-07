from datetime import datetime
from fpdf import FPDF
import streamlit as st
import os

# ---------------------------
# Configuração base
# ---------------------------
config = {
    "campo": {"rendimento": 200},
    "floresta": {"rendimento": 190},
}

custos_base = {
    "campo": {1: 0.0667, 2: 0.1334},
    "floresta": {1: 0.08491, 2: 0.16982},
}

IVA = 0.06  # ajusta se precisares

# ---------------------------
# UI Base
# ---------------------------
st.set_page_config(page_title="Simulador de Terrenos", layout="centered")
st.title("📊 Simulador de Limpeza de Terrenos")
st.markdown("Preenche os dados abaixo para obter uma estimativa:")

tipo = st.selectbox("🪓 Tipo de corte:", ["Campo", "Floresta"]).lower()
area = st.number_input("🧱 Área do terreno (m²):", min_value=0.0, step=10.0)
altura_cm = st.number_input("🌿 Altura da vegetação (cm):", min_value=0.0, step=1.0)
trabalhadores = st.number_input("👷 Nº de trabalhadores:", min_value=1, step=1)
margem = st.slider("📈 Margem de lucro (%):", min_value=0, max_value=100, value=25)

# ---------------------------
# Cálculo (margem embutida)
# ---------------------------
def calcular(tipo, area, altura_cm, trabalhadores, margem):
    trabalhadores = int(trabalhadores)
    rendimento = config[tipo]["rendimento"]
    custo_m2_base = custos_base[tipo][1 if trabalhadores == 1 else 2]

    fator_vegetacao = 1 + (max(0, int((altura_cm - 30) / 10)) * 0.10)

    tempo_horas = (area / rendimento) * fator_vegetacao / trabalhadores

    preco_m2_sem_iva_sem_margem = custo_m2_base * fator_vegetacao
    preco_total_sem_iva_sem_margem = preco_m2_sem_iva_sem_margem * area

    fator_margem = 1 + (margem / 100)
    preco_m2_sem_iva = preco_m2_sem_iva_sem_margem * fator_margem
    preco_total_sem_iva = preco_total_sem_iva_sem_margem * fator_margem

    preco_total_com_iva = preco_total_sem_iva * (1 + IVA)

    return tempo_horas, preco_m2_sem_iva, preco_total_sem_iva, preco_total_com_iva

# ---------------------------
# Helpers PDF
# ---------------------------
def _compact_lines(*items):
    out = []
    for it in items:
        if it is None:
            continue
        s = str(it).strip()
        if s:
            out.append(s)
    return out

def _try_load_unicode_fonts(pdf: FPDF):
    """
    Tenta carregar fontes Unicode (TTF).
    Se não existirem, usa fontes core e devolve False.
    """
    regular_path = os.path.join("fonts", "DejaVuSans.ttf")
    bold_path = os.path.join("fonts", "DejaVuSans-Bold.ttf")

    if os.path.exists(regular_path) and os.path.exists(bold_path):
        pdf.add_font("DejaVu", "", regular_path, uni=True)
        pdf.add_font("DejaVu", "B", bold_path, uni=True)
        return True

    return False

def _safe_text(text: str, unicode_ok: bool) -> str:
    """
    Se não houver fonte Unicode, evita caracteres problemáticos como €.
    """
    if unicode_ok:
        return text
    # fallback: troca € por EUR
    return text.replace("€", "EUR")

def _draw_block_right(pdf: FPDF, y: float, lines: list[str], unicode_ok: bool, box_w: float = 85):
    if not lines:
        return
    x = pdf.w - pdf.r_margin - box_w
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu" if unicode_ok else "Helvetica", "", 10)
    for line in lines:
        pdf.multi_cell(box_w, 5, _safe_text(line, unicode_ok))
        pdf.set_x(x)

def _draw_block_left(pdf: FPDF, y: float, lines: list[str], unicode_ok: bool, box_w: float = 120):
    if not lines:
        return
    x = pdf.l_margin
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu" if unicode_ok else "Helvetica", "", 10)
    for line in lines:
        pdf.multi_cell(box_w, 5, _safe_text(line, unicode_ok))
        pdf.set_x(x)

# ---------------------------
# PDF (layout + texto)
# ---------------------------
def gerar_pdf(
    tipo, area, altura_cm, trabalhadores,
    tempo_horas, preco_m2_sem_iva, preco_total_com_iva,
    empresa_nome="", empresa_nif="", empresa_morada="", empresa_tel="", empresa_email="",
    cliente_nome="", cliente_nif="", cliente_morada="", cliente_tel="", cliente_email="",
    obra_local="", validade_dias="", observacoes=""
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    unicode_ok = _try_load_unicode_fonts(pdf)

    font_regular = "DejaVu" if unicode_ok else "Helvetica"
    font_bold = "DejaVu" if unicode_ok else "Helvetica"

    # Título
    pdf.set_font(font_bold, "B", 16) if unicode_ok else pdf.set_font(font_bold, "B", 16)
    pdf.cell(0, 8, _safe_text("PROPOSTA DE ORÇAMENTO", unicode_ok), ln=1, align="L")

    pdf.set_font(font_regular, "", 10)
    pdf.cell(0, 6, _safe_text(f"Data: {datetime.now().strftime('%d/%m/%Y')}", unicode_ok), ln=1, align="L")

    # Empresa (canto superior direito)
    empresa_lines = _compact_lines(
        empresa_nome,
        f"NIF: {empresa_nif}" if empresa_nif else "",
        empresa_morada,
        f"Tel: {empresa_tel}" if empresa_tel else "",
        f"Email: {empresa_email}" if empresa_email else "",
    )
    _draw_block_right(pdf, y=10, lines=empresa_lines, unicode_ok=unicode_ok, box_w=85)

    # Cliente (por baixo, lado esquerdo)
    cliente_lines = _compact_lines(
        "Cliente:",
        cliente_nome,
        f"NIF: {cliente_nif}" if cliente_nif else "",
        cliente_morada,
        f"Tel: {cliente_tel}" if cliente_tel else "",
        f"Email: {cliente_email}" if cliente_email else "",
    )
    _draw_block_left(pdf, y=32, lines=cliente_lines, unicode_ok=unicode_ok, box_w=120)

    # Local da obra (opcional)
    y_after_cliente = 32 + (len(cliente_lines) * 5) + 2
    if obra_local.strip():
        pdf.set_xy(pdf.l_margin, y_after_cliente)
        pdf.set_font(font_bold, "B", 11) if unicode_ok else pdf.set_font(font_bold, "B", 11)
        pdf.cell(0, 6, _safe_text("Local da obra:", unicode_ok), ln=1)
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(obra_local.strip(), unicode_ok))
        y_after_cliente = pdf.get_y() + 2

    # Separador
    pdf.set_xy(pdf.l_margin, max(y_after_cliente, 55))
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    tipo_txt = "Campo" if tipo == "campo" else "Floresta"

    def write_section(title: str, body: str):
        pdf.set_font(font_bold, "B", 11) if unicode_ok else pdf.set_font(font_bold, "B", 11)
        pdf.multi_cell(0, 6, _safe_text(title, unicode_ok))
        pdf.ln(1)
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(body, unicode_ok))
        pdf.ln(2)

    write_section(
        "Enquadramento",
        "Na sequência do pedido de orçamento, apresentamos a nossa proposta para limpeza e controlo de vegetação, "
        "com intervenção profissional e execução orientada para segurança, eficiência e bom acabamento."
    )

    write_section(
        "Resumo técnico da intervenção",
        f"- Tipo de corte: {tipo_txt}\n"
        f"- Área estimada: {area:.0f} m²\n"
        f"- Altura média de vegetação: {altura_cm:.0f} cm\n"
        f"- Equipa prevista: {int(trabalhadores)} trabalhador(es)\n"
        f"- Tempo estimado de execução: {tempo_horas:.1f} horas"
    )

    write_section(
        "Metodologia de trabalho (etapas)",
        "1) Preparação do local e verificação de acessos, obstáculos e zonas sensíveis (muros, vedações, árvores, estruturas).\n"
        "2) Rocagem/corte da vegetação com controlo de projeções e proteção de áreas críticas.\n"
        "3) Acabamentos junto a limites, cantos, muros e zonas de maior detalhe.\n"
        "4) Inspeção final e ajuste de pontos que necessitem de reforço."
    )

    write_section(
        "Condições comerciais",
        f"- Preço por m² (sem IVA): {preco_m2_sem_iva:.4f} €\n"
        f"- Total a pagar (com IVA): {preco_total_com_iva:.2f} €"
    )

    if str(validade_dias).strip():
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(f"Validade do orçamento: {validade_dias.strip()} dias.", unicode_ok))
        pdf.ln(2)

    if str(observacoes).strip():
        pdf.set_font(font_bold, "B", 10) if unicode_ok else pdf.set_font(font_bold, "B", 10)
        pdf.cell(0, 6, _safe_text("Observações:", unicode_ok), ln=1)
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(observacoes.strip(), unicode_ok))
        pdf.ln(2)

    # Rodapé
    pdf.set_font(font_regular, "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4,
        _safe_text(
            "Nota: Valores estimados com base nos dados fornecidos. Poderão ser ajustados caso existam condicionantes "
            "não visíveis (acessos, declives, resíduos, obstáculos ou vegetação de densidade anormal).",
            unicode_ok
        )
    )

    return bytes(pdf.output(dest="S"))

# ---------------------------
# Cálculo
# ---------------------------
calcular_btn = st.button("📊 Calcular orçamento", use_container_width=True)

current_signature = (tipo, float(area), float(altura_cm), int(trabalhadores), int(margem))
if st.session_state.get("calc_signature") and st.session_state["calc_signature"] != current_signature:
    st.session_state.pop("calc_signature", None)
    st.session_state.pop("calc_results", None)

if calcular_btn:
    if area <= 0:
        st.error("A área tem de ser superior a 0 m².")
    else:
        tempo_horas, preco_m2_sem_iva, preco_total_sem_iva, preco_total_com_iva = calcular(
            tipo, area, altura_cm, int(trabalhadores), margem
        )

        st.session_state["calc_signature"] = current_signature
        st.session_state["calc_results"] = {
            "tipo": tipo,
            "area": float(area),
            "altura_cm": float(altura_cm),
            "trabalhadores": int(trabalhadores),
            "tempo_horas": float(tempo_horas),
            "preco_m2_sem_iva": float(preco_m2_sem_iva),
            "preco_total_sem_iva": float(preco_total_sem_iva),
            "preco_total_com_iva": float(preco_total_com_iva),
        }

# ---------------------------
# Resultados (texto) + Campos + Botão único (gera+descarrega)
# ---------------------------
if "calc_results" in st.session_state:
    r = st.session_state["calc_results"]
    tipo_txt = "Campo" if r["tipo"] == "campo" else "Floresta"

    st.markdown("### 🧾 Proposta de orçamento (resumo)")
    st.markdown(
        f"""
Apresenta-se uma proposta de orçamento para **limpeza e controlo de vegetação** do tipo **{tipo_txt}**, numa área estimada de **{r['area']:.0f} m²** com vegetação média de **{r['altura_cm']:.0f} cm**.

A intervenção está prevista para uma equipa de **{r['trabalhadores']} trabalhador(es)**, com um **tempo estimado de {r['tempo_horas']:.1f} horas**.

O valor proposto corresponde a **{r['preco_m2_sem_iva']:.4f} € por m² (sem IVA)**, totalizando **{r['preco_total_sem_iva']:.2f} € sem IVA** e **{r['preco_total_com_iva']:.2f} € com IVA**.
        """.strip()
    )

    st.divider()
    st.markdown("### ✍️ Detalhes do orçamento (opcional) — preencher só o necessário")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("#### Empresa (opcional)")
        empresa_nome = st.text_input("Nome da empresa", value="")
        empresa_nif = st.text_input("NIF", value="")
        empresa_morada = st.text_input("Morada", value="")
        empresa_tel = st.text_input("Telefone", value="")
        empresa_email = st.text_input("Email", value="")

    with colB:
        st.markdown("#### Cliente (opcional)")
        cliente_nome = st.text_input("Nome do cliente", value="")
        cliente_nif = st.text_input("NIF do cliente", value="")
        cliente_morada = st.text_input("Morada do cliente", value="")
        cliente_tel = st.text_input("Telefone do cliente", value="")
        cliente_email = st.text_input("Email do cliente", value="")

    st.markdown("#### Obra / detalhes (opcional)")
    obra_local = st.text_input("Local da obra", value="")
    validade_dias = st.text_input("Validade (dias)", value="")
    observacoes = st.text_area("Observações", value="", height=90)

    pdf_bytes = gerar_pdf(
        r["tipo"], r["area"], r["altura_cm"], r["trabalhadores"],
        r["tempo_horas"], r["preco_m2_sem_iva"], r["preco_total_com_iva"],
        empresa_nome=empresa_nome, empresa_nif=empresa_nif, empresa_morada=empresa_morada,
        empresa_tel=empresa_tel, empresa_email=empresa_email,
        cliente_nome=cliente_nome, cliente_nif=cliente_nif, cliente_morada=cliente_morada,
        cliente_tel=cliente_tel, cliente_email=cliente_email,
        obra_local=obra_local, validade_dias=validade_dias, observacoes=observacoes
    )

    st.download_button(
        label="🧾 Gerar e descarregar PDF",
        data=pdf_bytes,
        file_name=f"orcamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
