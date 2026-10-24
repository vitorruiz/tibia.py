# Sync local do snapshot do Char Bazaar (launchd)

O snapshot do Char Bazaar (`bazaar.json.gz`, publicado na release `bazaar-latest`) é gerado por
`scripts/bazaar_sync_local.sh`, que roda **no Mac** via launchd. O tibia.com responde 403 aos IPs dos runners
hospedados do GitHub Actions, então o workflow `bazaar-sync.yml` ficou só com disparo manual.

> Solução temporária: depende de o Mac estar ligado. A ideia é migrar para algo independente de uma máquina
> pessoal (ver [Migração futura](#migração-futura)).

## O que é instalado

| Item | Caminho |
| --- | --- |
| Agente do launchd | `~/Library/LaunchAgents/com.vitorruiz.bazaar-sync.plist` |
| Log | `~/Library/Logs/bazaar-sync.log` |
| Virtualenv usado pelo script | `venv/` na raiz do repositório |

O agente executa o script a cada hora e no login. Não é um daemon: o processo termina ao fim de cada execução, e a
maioria delas só confere que o snapshot já está em dia. O agente aponta para os scripts **dentro deste repositório**,
então o repo precisa continuar no mesmo caminho e numa branch que contenha `scripts/`.

## Instalar

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt certifi && venv/bin/pip install -e . --no-deps
gh auth status                      # o gh precisa estar autenticado com permissão de escrita no repo
./scripts/launchd/install.sh
```

Para verificar:

```bash
launchctl print gui/$(id -u)/com.vitorruiz.bazaar-sync | grep -E "state|last exit|runs"
tail -f ~/Library/Logs/bazaar-sync.log
launchctl kickstart gui/$(id -u)/com.vitorruiz.bazaar-sync   # força uma execução agora
```

Para rodar à mão fora do launchd (por exemplo, forçando antes do server save): `./scripts/bazaar_sync_local.sh --force`.

## Desinstalar completamente

1. Remover o agente (e o log):

   ```bash
   ./scripts/launchd/uninstall.sh --purge
   ```

   Equivale a:

   ```bash
   launchctl bootout gui/$(id -u)/com.vitorruiz.bazaar-sync
   rm ~/Library/LaunchAgents/com.vitorruiz.bazaar-sync.plist
   rm -f ~/Library/Logs/bazaar-sync.log
   ```

2. Confirmar que não sobrou nada:

   ```bash
   launchctl print gui/$(id -u)/com.vitorruiz.bazaar-sync   # deve falhar com "Could not find service"
   ls ~/Library/LaunchAgents | grep bazaar                  # não deve listar nada
   ```

3. Opcional, só se não for mais usar o sync local: apagar o virtualenv (`rm -rf venv`).

Depois de desinstalar, nada mais atualiza o snapshot. A release `bazaar-latest` continua publicada com o último
arquivo, e o `/exevo/auctions` segue servindo esses dados, mas os leilões novos deixam de entrar e os encerrados
são filtrados na consulta. Para não deixar o endpoint servindo dados desatualizados, só desinstale depois de ter
outra forma de gerar o snapshot.

## Migração futura

O que precisa ser trocado é **onde** o sync roda; o script `scripts/bazaar_sync.py` e o formato do snapshot
continuam os mesmos. Caminhos possíveis:

- **Runner self-hosted** (mini PC, Raspberry, VPS barata): o workflow `bazaar-sync.yml` já existe, bastando
  trocar `runs-on` e voltar o `schedule` (hoje removido).
- **GitHub Actions com proxy:** `tibiapy.Client` aceita `proxy_url` (SOCKS). Precisa de um proxy cujo IP o
  tibia.com não bloqueie, em geral um serviço residencial pago.
- **Servidor próprio ou VM gratuita** com IP que o tibia.com aceite: rodar `bazaar_sync_local.sh` por cron/systemd.

Antes de escolher, vale confirmar com um disparo manual que o IP do novo ambiente não recebe 403 do tibia.com.
Ao migrar, desinstale o agente seguindo a seção acima para não haver dois geradores publicando na mesma release.
