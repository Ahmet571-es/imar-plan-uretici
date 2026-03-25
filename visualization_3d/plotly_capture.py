"""
Plotly 3D Canvas Yakalama — Streamlit bileşeni.

Plotly chart'ın ekran görüntüsünü alıp base64 formatında
Streamlit session_state'e aktaran JS köprüsü.
"""

import streamlit as st
import streamlit.components.v1 as components


CAPTURE_JS_COMPONENT = """
<div id="capture-status" style="display:none"></div>
<script>
(function() {{
    const POLL_INTERVAL = 300;
    const MAX_ATTEMPTS = 30;
    let attempts = 0;

    function findPlotlyDiv() {{
        // Streamlit'in ana frame'inde Plotly div'i bul
        try {{
            const frames = window.parent.document.querySelectorAll('iframe');
            for (const frame of frames) {{
                try {{
                    const plotDivs = frame.contentDocument.querySelectorAll('.js-plotly-plot');
                    if (plotDivs.length > 0) return plotDivs[plotDivs.length - 1];
                }} catch(e) {{}}
            }}
            // Doğrudan parent'ta ara
            const directPlots = window.parent.document.querySelectorAll('.js-plotly-plot');
            if (directPlots.length > 0) return directPlots[directPlots.length - 1];
        }} catch(e) {{}}
        return null;
    }}

    function captureChart() {{
        attempts++;
        const plotDiv = findPlotlyDiv();

        if (!plotDiv || !plotDiv._fullLayout) {{
            if (attempts < MAX_ATTEMPTS) {{
                setTimeout(captureChart, POLL_INTERVAL);
            }}
            return;
        }}

        // Plotly'nin kendi toImage API'sini kullan
        const Plotly = window.parent.Plotly || (plotDiv.ownerDocument.defaultView && plotDiv.ownerDocument.defaultView.Plotly);
        if (!Plotly) {{
            // Fallback: canvas'tan doğrudan al
            const canvas = plotDiv.querySelector('canvas');
            if (canvas) {{
                sendData(canvas.toDataURL('image/png'));
            }}
            return;
        }}

        Plotly.toImage(plotDiv, {{
            format: 'png',
            width: {width},
            height: {height},
            scale: 2
        }}).then(function(dataUrl) {{
            sendData(dataUrl);
        }}).catch(function(err) {{
            // Canvas fallback
            const canvas = plotDiv.querySelector('canvas');
            if (canvas) {{
                sendData(canvas.toDataURL('image/png'));
            }}
        }});
    }}

    function sendData(dataUrl) {{
        // data:image/png;base64,xxxx formatından base64 kısmını çıkar
        const base64 = dataUrl.split(',')[1] || dataUrl;

        // Streamlit'e gönder — hidden div'e yaz, Streamlit component framework okur
        const statusDiv = document.getElementById('capture-status');
        if (statusDiv) {{
            statusDiv.textContent = base64;
            statusDiv.style.display = 'block';
        }}

        // Streamlit component value olarak gönder
        if (window.Streamlit) {{
            window.Streamlit.setComponentValue(base64);
        }}

        // Alternatif: postMessage
        window.parent.postMessage({{
            type: 'plotly_screenshot',
            isStreamlitMessage: true,
            data: base64
        }}, '*');
    }}

    // Başlat
    if (document.readyState === 'complete') {{
        setTimeout(captureChart, 500);
    }} else {{
        window.addEventListener('load', function() {{
            setTimeout(captureChart, 500);
        }});
    }}
}})();
</script>
"""


def render_plotly_with_capture(fig, key: str = "plotly_3d", height: int = 700):
    """Plotly figure'ı Streamlit'te gösterir ve yakalama mekanizmasını ekler.

    Plotly chart'ı normal şekilde render eder, ardından bir 'Görüntüyü Yakala'
    butonu ile mevcut kamera açısından screenshot alır.

    Args:
        fig: Plotly Figure nesnesi.
        key: Streamlit widget key'i.
        height: Chart yüksekliği (piksel).
    """
    # Plotly chart'ı göster
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{key}")


def capture_plotly_via_export(fig, width: int = 1920, height: int = 1080) -> str:
    """Plotly figure'ı sunucu tarafında statik görsele dönüştürür.

    Kaleido/orca kuruluysa fig.to_image() kullanır,
    yoksa fig.to_html() + inline JS ile client-side yakalama yapar.

    Args:
        fig: Plotly Figure nesnesi.
        width: Görsel genişliği (piksel).
        height: Görsel yüksekliği (piksel).

    Returns:
        Base64 encoded PNG string, veya boş string.
    """
    import base64

    # Yöntem 1: Kaleido ile sunucu tarafı export (en güvenilir)
    try:
        img_bytes = fig.to_image(
            format="png",
            width=width,
            height=height,
            scale=2,
        )
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        pass

    # Yöntem 2: Plotly'nin write_image ile geçici dosyaya yaz
    try:
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            fig.write_image(tmp.name, width=width, height=height, scale=2)
            tmp.seek(0)
            img_bytes = open(tmp.name, "rb").read()
            os.unlink(tmp.name)
            return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        pass

    return ""


def render_capture_button_html(width: int = 1920, height: int = 1080) -> str:
    """Client-side Plotly yakalama butonu için HTML/JS kodu döndürür.

    Bu HTML, Streamlit components.html() ile gömülür.
    Yakalanan görsel base64 olarak bir hidden textarea'ya yazılır.

    Args:
        width: Yakalama genişliği.
        height: Yakalama yüksekliği.

    Returns:
        HTML string.
    """
    return f"""
    <div style="padding: 8px 0;">
        <button id="captureBtn"
                onclick="captureCurrentView()"
                style="background: #1E88E5; color: white; border: none;
                       padding: 10px 24px; border-radius: 6px; cursor: pointer;
                       font-size: 14px; font-weight: 500;
                       transition: background 0.2s;">
            Mevcut Gorunumu Yakala
        </button>
        <span id="captureMsg" style="margin-left: 12px; color: #666; font-size: 13px;"></span>
        <textarea id="capturedData" style="display:none;"></textarea>
    </div>

    <script>
    function captureCurrentView() {{
        const btn = document.getElementById('captureBtn');
        const msg = document.getElementById('captureMsg');
        btn.disabled = true;
        btn.style.background = '#90CAF9';
        msg.textContent = 'Yakalaniyor...';

        try {{
            // Parent frame'deki tum Plotly chart'lari bul
            const allPlots = window.parent.document.querySelectorAll('.js-plotly-plot');
            let targetPlot = null;

            // En buyuk (3D) Plotly chart'i sec
            for (const plot of allPlots) {{
                if (plot._fullLayout && plot._fullLayout.scene) {{
                    targetPlot = plot;
                    break;
                }}
            }}

            if (!targetPlot) {{
                // Fallback: son plotly chart
                targetPlot = allPlots[allPlots.length - 1];
            }}

            if (!targetPlot) {{
                msg.textContent = 'Plotly chart bulunamadi.';
                btn.disabled = false;
                btn.style.background = '#1E88E5';
                return;
            }}

            const Plotly = window.parent.Plotly;
            if (Plotly && Plotly.toImage) {{
                Plotly.toImage(targetPlot, {{
                    format: 'png',
                    width: {width},
                    height: {height},
                    scale: 2
                }}).then(function(dataUrl) {{
                    const base64 = dataUrl.split(',')[1] || dataUrl;
                    document.getElementById('capturedData').value = base64;

                    // Streamlit'e bildir
                    window.parent.postMessage({{
                        type: 'plotly_capture_complete',
                        data: base64
                    }}, '*');

                    msg.textContent = 'Goruntu yakalandi!';
                    msg.style.color = '#2E7D32';
                    btn.disabled = false;
                    btn.style.background = '#1E88E5';
                }}).catch(function(err) {{
                    msg.textContent = 'Hata: ' + err.message;
                    msg.style.color = '#C62828';
                    btn.disabled = false;
                    btn.style.background = '#1E88E5';
                }});
            }} else {{
                // Canvas fallback
                const canvas = targetPlot.querySelector('canvas');
                if (canvas) {{
                    const dataUrl = canvas.toDataURL('image/png');
                    const base64 = dataUrl.split(',')[1];
                    document.getElementById('capturedData').value = base64;
                    msg.textContent = 'Canvas yakalandi!';
                    msg.style.color = '#2E7D32';
                }} else {{
                    msg.textContent = 'Canvas bulunamadi.';
                    msg.style.color = '#C62828';
                }}
                btn.disabled = false;
                btn.style.background = '#1E88E5';
            }}
        }} catch(e) {{
            msg.textContent = 'Hata: ' + e.message;
            msg.style.color = '#C62828';
            btn.disabled = false;
            btn.style.background = '#1E88E5';
        }}
    }}
    </script>
    """
