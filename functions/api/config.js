export function onRequestGet({data}) {
  return Response.json({enabled:true, owner:data.owner});
}
