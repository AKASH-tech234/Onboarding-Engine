export function formatDuration(hrs) {
  if (!hrs || hrs === 0) return "0m";
  if (hrs < 1) return `${Math.round(hrs * 60)}m`;
  if (Number.isInteger(hrs)) return `${hrs}h`;
  
  const h = Math.floor(hrs);
  const m = Math.round((hrs % 1) * 60);
  return `${h}h ${m}m`;
}
