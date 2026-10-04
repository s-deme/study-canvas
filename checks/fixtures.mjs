// Synthetic fixtures exercise the application without distributing teaching material.
export const questions = Array.from({length:240}, (_,i) => ({
  id:`custom:check-${i}`, category:i%10, topic:`検証項目${i}`,
  prompt:`検証${i}：選択肢Aを選んでください。`,
  options:['選択肢A','選択肢B','選択肢C','選択肢D'], answer:0,
  explanation:'採点と保存の動作を確認するためのデータです。', source:'自動チェック用ダミーデータ'
}));
