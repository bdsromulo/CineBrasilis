document.addEventListener("DOMContentLoaded", () => {
    carregarFilmes();
});

let todosFilmes = [];
let paginaAtual = 1;
const filmesPorPagina = 12; // Define quantos filmes aparecem por página

async function carregarFilmes() {
    try {
        const response = await fetch("../data/filmes.json");
        todosFilmes = await response.json();
        
        renderizarPagina(paginaAtual);
    } catch (error) {
        console.error("Erro ao carregar filmes:", error);
    }
}

function renderizarPagina(pagina) {
    const grid = document.getElementById("catalogo-grid");
    if (!grid) return;
    
    // Limpa a tela antes de colocar as novas cartas
    grid.innerHTML = ""; 
    
    // Matemática da Paginação
    // Se estou na página 1: inicia no 0 e vai até o 12
    // Se estou na página 2: inicia no 12 e vai até 24
    const indexInicio = (pagina - 1) * filmesPorPagina;
    const indexFim = indexInicio + filmesPorPagina;
    
    // Recorta exatamente aquele pedaço do array gigantesco de filmes
    const filmesDaPagina = todosFilmes.slice(indexInicio, indexFim);
    
    filmesDaPagina.forEach(filme => {
        grid.appendChild(criarCardFilme(filme));
    });
    
    // Atualiza os botões lá no final
    renderizarControlesPaginacao();
}

function renderizarControlesPaginacao() {
    const container = document.getElementById("paginacao-container");
    if (!container) return;

    container.innerHTML = ""; // Limpa antigos controles
    
    const totalPaginas = Math.ceil(todosFilmes.length / filmesPorPagina);
    
    // Botão "Anterior"
    const btnAnterior = document.createElement("button");
    btnAnterior.textContent = "❮ Anterior";
    btnAnterior.className = "btn-paginacao";
    // Desabilita o botão se já estivermos na página 1
    btnAnterior.disabled = paginaAtual === 1;
    btnAnterior.addEventListener("click", () => {
        if (paginaAtual > 1) {
            paginaAtual--;
            renderizarPagina(paginaAtual);
            window.scrollTo({ top: 0, behavior: 'smooth' }); // Volta ao topo da página suavemente
        }
    });
    container.appendChild(btnAnterior);

    // Indicador de Página numérico (Ex: Página 1 de 5)
    const textoPagina = document.createElement("span");
    textoPagina.className = "texto-paginacao";
    textoPagina.textContent = `Página ${paginaAtual} de ${totalPaginas}`;
    container.appendChild(textoPagina);

    // Botão "Próximo"
    const btnProximo = document.createElement("button");
    btnProximo.textContent = "Próxima ❯";
    btnProximo.className = "btn-paginacao";
    // Desabilita se estivermos na última página possível
    btnProximo.disabled = paginaAtual === totalPaginas;
    btnProximo.addEventListener("click", () => {
        if (paginaAtual < totalPaginas) {
            paginaAtual++;
            renderizarPagina(paginaAtual);
            window.scrollTo({ top: 0, behavior: 'smooth' }); // Volta ao topo da página suavemente
        }
    });
    container.appendChild(btnProximo);
}

