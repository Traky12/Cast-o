/**
 * CASTÚO-SYSTEM™ — Políticas de timelock para cambios críticos (Defender)
 * HSM address: 48h | Owner: 72h + 3 firmantes | Upgrade contrato: 24h + auditoría
 */
const { Defender } = require('defender-sdk');

async function setTimelockPolicies() {
  const defender = new Defender({
    apiKey: process.env.DEFENDER_API_KEY,
    apiSecret: process.env.DEFENDER_API_SECRET,
  });

  const policyId = process.env.DEFENDER_POLICY_ID || 'GaiaChainValidator-Upgrade-Policy';
  if (!policyId) {
    console.warn('DEFENDER_POLICY_ID no definido.');
    return { ok: true, message: 'Stub: configure DEFENDER_POLICY_ID and uncomment' };
  }

  // 1. Cambio de dirección HSM — 48 horas
  // await defender.client.createPolicyRule({
  //   policyId,
  //   rule: {
  //     name: 'HSM-Address-Change-Timelock',
  //     type: 'timelock',
  //     params: {
  //       delay: 172800,
  //       function: 'setHSMAddress',
  //       proposers: [process.env.DEFENDER_ADMIN_ADDRESS],
  //       executors: [process.env.DEFENDER_EXECUTOR_ADDRESS],
  //     },
  //   },
  // });

  // 2. Cambio de owner — 72 horas + 3 firmantes
  // await defender.client.createPolicyRule({
  //   policyId,
  //   rule: {
  //     name: 'Owner-Change-Timelock',
  //     type: 'timelock',
  //     params: {
  //       delay: 259200,
  //       function: 'transferOwnership',
  //       proposers: [process.env.DEFENDER_SIGNER_1, process.env.DEFENDER_SIGNER_2, process.env.DEFENDER_SIGNER_3].filter(Boolean),
  //       executors: [process.env.DEFENDER_EXECUTOR_ADDRESS],
  //     },
  //   },
  // });

  // 3. Upgrade de contrato — 24 horas
  // await defender.client.createPolicyRule({
  //   policyId,
  //   rule: {
  //     name: 'Contract-Upgrade-Timelock',
  //     type: 'timelock',
  //     params: {
  //       delay: 86400,
  //       function: 'upgradeTo',
  //       proposers: [process.env.DEFENDER_ADMIN_ADDRESS],
  //       executors: [process.env.DEFENDER_EXECUTOR_ADDRESS],
  //     },
  //   },
  // });

  console.log('Timelock policies (stub). Descomentar y definir variables.');
  return { ok: true };
}

setTimelockPolicies().catch(console.error);
module.exports = { setTimelockPolicies };
