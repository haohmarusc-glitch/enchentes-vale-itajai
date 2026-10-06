import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import estilos from './TelaAcessos.module.css'

/**
 * Quem está logado e quem entrou no site — só para o admin (pedido do Jefferson, 06/10/2026).
 *
 * A lista vem de `/api/acessos`, que responde 404 a quem não está em `ADMIN_EMAILS`: para essa
 * pessoa, esta tela diz só "página não encontrada". Nenhum link do site aponta para cá.
 */
interface Registro {
  email: string
  primeiro: string
  ultimo: string
  dias: number
}
interface Lista {
  gerado_em: string
  agora: Registro[]
  todos: Registro[]
  agora_min: number
  retencao_dias: number
  erro?: string
}

const FUSO = 'America/Sao_Paulo'
const quando = (iso: string) =>
  new Date(iso).toLocaleString('pt-BR', { timeZone: FUSO, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

function haQuanto(iso: string, agora: Date): string {
  const min = Math.max(0, Math.round((agora.getTime() - Date.parse(iso)) / 60_000))
  if (min < 60) return `há ${min} min`
  const h = Math.round(min / 60)
  if (h < 48) return `há ${h} h`
  return `há ${Math.round(h / 24)} dias`
}

export default function TelaAcessos() {
  const [estado, setEstado] = useState<'carregando' | 'negado' | 'erro' | Lista>('carregando')

  useEffect(() => {
    let vivo = true
    fetch('/api/acessos', { credentials: 'same-origin', headers: { accept: 'application/json' } })
      .then(async (r) => {
        if (!vivo) return
        if (r.status === 404) return setEstado('negado')
        if (!r.ok) return setEstado('erro')
        const tipo = r.headers.get('content-type') ?? ''
        if (!tipo.includes('json')) return setEstado('negado') // site publicado sem a função: tela de login ou o app
        setEstado((await r.json()) as Lista)
      })
      .catch(() => vivo && setEstado('erro'))
    return () => {
      vivo = false
    }
  }, [])

  if (estado === 'carregando') return <p className={estilos.nota}>Carregando…</p>
  if (estado === 'negado')
    return (
      <p className={estilos.nota}>
        Página não encontrada. <Link to="/">Voltar ao início</Link>
      </p>
    )
  if (estado === 'erro') return <p className={estilos.nota}>Não foi possível carregar a lista de acessos. Tente de novo.</p>

  const agora = new Date(estado.gerado_em)
  return (
    <>
      <p className={estilos.voltar}>
        <Link to="/">← Início</Link>
      </p>
      <h1 className={estilos.titulo}>Acessos ao site</h1>
      <p className={estilos.nota}>
        Só o admin vê esta página. Para cada e-mail que passou pelo login: o primeiro e o último acesso e em quantos dias
        entrou. Horário de Brasília. O registro de quem não volta é apagado em {estado.retencao_dias} dias.
      </p>
      {estado.erro === 'sem_kv' && (
        <p className={estilos.aviso}>O armazenamento (KV CHAT_IA) não está ligado neste deploy: nada é registrado.</p>
      )}

      <h2 className={estilos.subtitulo}>
        Logados agora <span className={estilos.contagem}>(vistos nos últimos {estado.agora_min} min: {estado.agora.length})</span>
      </h2>
      {estado.agora.length ? (
        <ul className={estilos.lista}>
          {estado.agora.map((r) => (
            <li key={r.email}>
              <strong>{r.email}</strong> — {haQuanto(r.ultimo, agora)}
            </li>
          ))}
        </ul>
      ) : (
        <p className={estilos.nota}>Ninguém nos últimos {estado.agora_min} minutos.</p>
      )}

      <h2 className={estilos.subtitulo}>
        Quem entrou <span className={estilos.contagem}>({estado.todos.length})</span>
      </h2>
      <div className={estilos.rolagem}>
        <table className={estilos.tabela}>
          <thead>
            <tr>
              <th scope="col">E-mail</th>
              <th scope="col">Último acesso</th>
              <th scope="col">Primeiro acesso</th>
              <th scope="col">Dias</th>
            </tr>
          </thead>
          <tbody>
            {estado.todos.map((r) => (
              <tr key={r.email}>
                <td>{r.email}</td>
                <td>
                  {quando(r.ultimo)} <span className={estilos.contagem}>({haQuanto(r.ultimo, agora)})</span>
                </td>
                <td>{quando(r.primeiro)}</td>
                <td className={estilos.numero}>{r.dias}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={estilos.nota}>
        "Logado agora" quer dizer que abriu uma página nos últimos {estado.agora_min} minutos. O login em si (com IP e
        país) fica no painel da Cloudflare: Zero Trust → Logs → Access.
      </p>
    </>
  )
}
