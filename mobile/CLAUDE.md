# mobile

Contrato de trabalho do app Flutter, o único cliente do produto. O que vale para o repositório
inteiro está no [CLAUDE.md da raiz](../CLAUDE.md); o porquê, nas [decisões](../docs/decisoes/).

**Antes de mexer numa tela ou rota, leia [app/interface](../docs/app/interface.md).** Armadilhas e revisão
de telas: [app/desenvolvimento](../docs/app/desenvolvimento.md).

```bash
flutter analyze && flutter test
flutter build apk --release
python tool/build_icons.py --check
```

- **Não rode `dart format`** — reescreve o `design_tokens.dart` e quebra os `if`s de uma linha.
- **`analyze` e `test` nunca tocam o Gradle.** O build Android é outra metade, e é o comando que
  ninguém roda. Obrigatório ao mexer em plugin, `pubspec.yaml` ou `mobile/android/`.

---

## Invariantes

- **O app delega.** Regra de negócio vive no backend; nenhuma tela decide leitura de valor.
- **A navegação é o ciclo do dinheiro:** `/mes` → `/sobra` → `/patrimonio`, mais `/descobrir` e
  `/voce`. URLs antigas seguem como redirect — link salvo é contrato.
- **A paleta mora só em `design_tokens.dart`.** Não escreva hexadecimal em `theme.dart`.
- **Papel de cor novo se declara nos dois temas.**
- **Estado ≠ direção.** `fiStateColor` para julgamento, `fiDirectionColor` para aritmética.
- **Tipo é papel, não tamanho.** `fontSize:` solto tem catraca em zero.
- **Serifa decide, sans mede.**
- **Fio + chão, não card + card.** A caixa é `FiObject`, e só para objeto. `Card`, `ListTile`,
  `SwitchListTile`, `CircleAvatar` estão em catraca zero.
- **Controle vem do sistema.** `Switch`, `Slider`, chips e `ExpansionTile` do Material só existem
  dentro de `core/widgets/` (`FiSwitch`, `FiSlider`, `FiChoiceChip`, `FiDisclosure`); `InkWell` e
  `GestureDetector` fora dele estão em catraca. Gráfico vem com tabela equivalente.
- **Julgamento exige explicabilidade.** Escape só com `// design-exception: regra — motivo`.
- **Estado de tela é contrato:** `AsyncValue.when` com `FiSkeleton`/`FiErrorState`. A falha guarda o
  **erro**, não um booleano. Vazio e falha nunca compartilham a mesma tela.
- **Falha usa `fiErrorMessage`**, nunca texto solto.
- **Preço vem com `formatAge`.** Em lista, o carimbo é o **mais antigo**.
- **Espera é `FiSkeleton.screen()`**, nunca disco girando.
- **Número em português é do formatador**, não do template — na saída e na entrada (`parseDecimal`).
- **Escrita tem retorno:** `fiAttempt` dá o erro e o sucesso; destrutivo confirma com `fiConfirm`.

---

## Armadilhas que não quebram o build

- **Papel de cor usado como o outro papel** faz uma perda aparecer como aviso.
- **Regra de lint que filtra por extensão não roda.** A regra varre `lib/`; o que estiver fora não é
  conferido. Confira contra o que o repositório tem.

---

## Ao adicionar…

| O quê | Faça também |
|---|---|
| Tela ou rota | Ler [app/interface](../docs/app/interface.md) antes |
| Dependência no `pubspec.yaml` | `flutter build apk --release` |
| Papel de cor | Declará-lo nos dois temas |
