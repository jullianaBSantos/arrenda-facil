from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os

app = FastAPI()

# Adiciona o Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos os domínios (para testes)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)

# Configuração do banco de dados MySQL
DATABASE_URL = "mysql+pymysql://root@localhost/arrendafacil"
engine = create_engine('mysql+pymysql://root@localhost/arrendafacil')
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()       

# Configuração do FastAPI e segurança
token_secret = "chave_secreta"
token_algorithm = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Definindo o OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Modelos do banco de dados
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(100))
    role = Column(String(10))  # "inquilino" ou "senhorio"

class Conta(Base):
    __tablename__ = "contas"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255))
    valor = Column(Integer)
    vencimento = Column(Date)  # Alterado para o tipo DATE
    paga = Column(Boolean, default=False)
    inquilino_id = Column(Integer, ForeignKey("users.id"))
    inquilino = relationship("User")

Base.metadata.create_all(bind=engine)

# Função para criar sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para gerar hash de senha
def hash_senha(senha: str):
    return password_context.hash(senha)

# Função para verificar senha
def verificar_senha(senha: str, hash_senha: str):
    return password_context.verify(senha, hash_senha)

# Função para gerar token JWT
def criar_token(user_id: int):
    exp = datetime.utcnow() + timedelta(hours=1)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, token_secret, algorithm=token_algorithm)

# Função para obter o usuário a partir do token JWT
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, token_secret, algorithms=[token_algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        usuario = db.query(User).filter(User.id == user_id).first()
        if usuario is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return usuario
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Criar usuário (registro)
@app.post("/register/")
def register(username: str, password: str, role: str, db: Session = Depends(get_db)):
    usuario_existente = db.query(User).filter(User.username == username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    usuario = User(username=username, password_hash=hash_senha(password), role=role)
    db.add(usuario)
    db.commit()
    return {"msg": "Usuário criado com sucesso"}

# Login e geração de token
@app.post("/login/")
def login(username: str, password: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.username == username).first()
    if not usuario or not verificar_senha(password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = criar_token(usuario.id)
    return {"token": token}

# Criar nova conta para pagamento
@app.post("/contas/")
def criar_conta(descricao: str, valor: int, vencimento: str, inquilino_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validar formato de vencimento
    try:
        vencimento_date = datetime.strptime(vencimento, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de vencimento inválido, use YYYY-MM-DD")
    
    conta = Conta(descricao=descricao, valor=valor, vencimento=vencimento_date, inquilino_id=inquilino_id)
    db.add(conta)
    db.commit()
    return {"msg": "Conta criada com sucesso", "conta_id": conta.id}

# Listar contas pendentes
@app.get("/contas/")
def listar_contas(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contas = db.query(Conta).filter_by(paga=False).all()
    return contas

# Marcar conta como paga
@app.put("/contas/{conta_id}/pagar")
def pagar_conta(conta_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conta = db.query(Conta).filter(Conta.id == conta_id).first()
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    conta.paga = True
    db.commit()
    return {"msg": "Conta marcada como paga", "conta_id": conta.id, "status": conta.paga}

# Envio de comprovante
@app.post("/comprovantes/")
def upload_comprovante(file: UploadFile = File(...)):
    # Validar tipo de arquivo
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Somente arquivos PDF são permitidos.")
    
    # Validar tamanho do arquivo (exemplo: até 5 MB)
    if file.file.tell() > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="O arquivo é muito grande.")
    
    # Salvar o arquivo no diretório
    os.makedirs("comprovantes", exist_ok=True)
    file_location = f"comprovantes/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())
    
    return {"msg": "Comprovante enviado com sucesso", "file_location": file_location}
