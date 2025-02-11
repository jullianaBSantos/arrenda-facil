let token = localStorage.getItem('token') || '';

// ✅ Função para fazer login
document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://127.0.0.1:8000/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
            const data = await response.json();
            token = data.token;
            localStorage.setItem('token', token); // Salva o token no navegador
            alert('Login bem-sucedido!');
            listarContas();
        } else {
            alert('Credenciais inválidas. Tente novamente.');
        }
    } catch (error) {
        console.error('Erro ao conectar ao servidor:', error);
        alert('Erro ao conectar ao servidor.');
    }
};

// ✅ Função para registrar novo usuário
document.getElementById('registerForm').onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const role = document.getElementById('role').value;

    try {
        const response = await fetch('http://127.0.0.1:8000/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role }),
        });

        if (response.ok) {
            alert('Usuário registrado com sucesso! Faça login para continuar.');
        } else {
            alert('Erro ao registrar usuário.');
        }
    } catch (error) {
        console.error('Erro ao conectar ao servidor:', error);
        alert('Erro ao registrar usuário.');
    }
};

// ✅ Função para listar contas pendentes e pagas
async function listarContas() {
    if (!token) {
        alert('Você precisa estar logado para visualizar as contas.');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/contas/', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` },
        });

        if (response.ok) {
            const contas = await response.json();
            const lista = document.getElementById('contasLista');
            lista.innerHTML = ''; // Limpa a lista antes de atualizar

            contas.forEach(conta => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>Descrição:</strong> ${conta.descricao}, 
                    <strong>Valor:</strong> R$${conta.valor}, 
                    <strong>Vencimento:</strong> ${conta.vencimento}, 
                    <strong>Status:</strong> ${conta.paga ? 'Paga' : 'Pendente'}
                    ${!conta.paga ? `<button onclick="marcarComoPaga(${conta.id})">Marcar como paga</button>` : ''}
                `;
                lista.appendChild(li);
            });
        } else {
            alert('Erro ao carregar contas.');
        }
    } catch (error) {
        console.error('Erro ao conectar ao servidor:', error);
        alert('Erro ao carregar contas.');
    }
}

// ✅ Função para marcar uma conta como paga
async function marcarComoPaga(contaId) {
    if (!token) {
        alert('Você precisa estar logado para realizar esta ação.');
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/contas/${contaId}/pagar`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            alert('Conta marcada como paga!');
            listarContas(); // Atualiza a lista de contas
        } else {
            alert('Erro ao atualizar o status da conta.');
        }
    } catch (error) {
        console.error('Erro ao conectar ao servidor:', error);
        alert('Erro ao processar o pagamento.');
    }
}

// ✅ Verifica se o usuário está logado ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        listarContas();
    }
});
