document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.querySelector(".menu-toggle");
    const themeToggle = document.querySelector(".theme-toggle");
    const themeIcon = document.querySelector(".theme-icon");
    const themeLabel = document.querySelector(".theme-label");

    document.querySelectorAll(".clinic-hero-image").forEach((imagem) => {
        const ocultarImagemIndisponivel = () => {
            imagem.classList.add("image-unavailable");
            imagem.parentElement?.classList.add("hero-without-image");
        };
        imagem.addEventListener("error", ocultarImagemIndisponivel);
        if (imagem.complete && imagem.naturalWidth === 0) {
            ocultarImagemIndisponivel();
        }
    });

    document.querySelectorAll('input[name="telefone"]').forEach((campo) => {
        const formatarTelefone = (valor) => {
            let digitos = valor.replace(/\D/g, "");
            if ((digitos.length === 12 || digitos.length === 13) && digitos.startsWith("55")) {
                digitos = digitos.slice(2);
            } else {
                digitos = digitos.slice(0, 11);
            }

            if (!digitos) return "";
            if (digitos.length <= 2) {
                return `(${digitos}${digitos.length === 2 ? ")" : ""}`;
            }

            const ddd = digitos.slice(0, 2);
            const numero = digitos.slice(2);
            const tamanhoPrefixo = numero.startsWith("9") ? 5 : 4;
            if (numero.length <= tamanhoPrefixo) {
                return `(${ddd}) ${numero}`;
            }
            return `(${ddd}) ${numero.slice(0, tamanhoPrefixo)}-${numero.slice(tamanhoPrefixo)}`;
        };

        const aplicarMascara = () => {
            const posicao = campo.selectionStart ?? campo.value.length;
            const digitosAtePosicao = campo.value.slice(0, posicao).replace(/\D/g, "").length;
            const formatado = formatarTelefone(campo.value);
            campo.value = formatado;

            let novaPosicao = 0;
            let digitosEncontrados = 0;
            while (novaPosicao < formatado.length && digitosEncontrados < digitosAtePosicao) {
                if (/\d/.test(formatado[novaPosicao])) digitosEncontrados += 1;
                novaPosicao += 1;
            }
            if (campo === document.activeElement) {
                campo.setSelectionRange(novaPosicao, novaPosicao);
            }
        };

        campo.addEventListener("input", aplicarMascara);
        aplicarMascara();
    });

    if (themeToggle) {
        const aplicarTema = (tema) => {
            const escuro = tema === "dark";
            document.documentElement.dataset.theme = escuro ? "dark" : "light";
            themeToggle.setAttribute("aria-label", escuro ? "Ativar modo claro" : "Ativar modo escuro");
            themeToggle.setAttribute("aria-pressed", String(escuro));
            if (themeIcon) themeIcon.textContent = escuro ? "☀" : "☾";
            if (themeLabel) themeLabel.textContent = escuro ? "Modo claro" : "Modo escuro";
        };

        aplicarTema(document.documentElement.dataset.theme || "light");
        themeToggle.addEventListener("click", () => {
            const novoTema = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            localStorage.setItem("clinica-tema", novoTema === "dark" ? "escuro" : "claro");
            aplicarTema(novoTema);
        });
    }

    if (sidebar && menuToggle) {
        menuToggle.addEventListener("click", () => {
            const aberto = sidebar.classList.toggle("sidebar-open");
            menuToggle.setAttribute("aria-expanded", String(aberto));
        });
    }

    document.querySelectorAll("form[data-confirm]").forEach((formulario) => {
        formulario.addEventListener("submit", (evento) => {
            if (!window.confirm(formulario.dataset.confirm)) {
                evento.preventDefault();
            }
        });
    });

    document.querySelectorAll(".flash-close").forEach((botao) => {
        botao.addEventListener("click", () => botao.closest(".flash")?.remove());
    });
});
