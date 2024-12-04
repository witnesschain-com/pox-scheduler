const axios = require('axios')
const fs = require('fs')
const { ethers } = require('ethers')

function getFlag(flag) {
  const flagIndex = process.argv.findIndex((arg) => arg === flag)
  if (flagIndex === -1) {
    return null
  }
  return process.argv[flagIndex + 1]
}

async function preLogin(proofType = 'pob') {
  const privateKey = fs.readFileSync('key', 'utf8').trim()
  const wallet = new ethers.Wallet(privateKey)
  console.log({ address: wallet.address })

  const preloginBody = {
    publicKey: wallet.address,
    walletPublicKey: {
      ethereum: wallet.address
    },
    keyType: 'ethereum',
    role: 'payer',
    claims: {
      downlink_bandwidth: '10',
      uplink_bandwidth: '10'
    }
  }

  // Pre-login
  console.log('Pre-login...')
  const preloginResponse = await axios.post(
    `https://api.witnesschain.com/proof/v1/pob/pre-login`,
    preloginBody
  )

  // Get the message
  const message = preloginResponse.data.result.message
  console.log({ result: message })

  // Get the cookies
  const preloginCookies = preloginResponse.headers['set-cookie'].filter(
    (cookie) => cookie.startsWith('__Secure-proof')
  )
  //   console.log({ preloginCookies })

  return { message, preloginCookies, wallet }
}

async function login(proofType = 'pob') {
  const { message, preloginCookies, wallet } = await preLogin(proofType)

  // Sign the message
  const signature = await wallet.signMessage(message)
  console.log({ signature })

  const loginBody = {
    signature
  }

  // Login
  console.log('Login...')
  const loginResponse = await axios.post(
    `https://api.witnesschain.com/proof/v1/${proofType}/login`,
    loginBody,
    {
      headers: {
        Cookie: preloginCookies
      }
    }
  )
  console.log('LOGIN', loginResponse.data)

  // get cookies
  const loginCookies = loginResponse.headers['set-cookie']

  return { loginCookies }
}

async function triggerChallenge(proofType = 'pob') {
  const { loginCookies } = await login(proofType)

  const challengeId = getFlag('--challenge-id')
  console.log({ challengeId })
  if (!challengeId) {
    console.log('--challenge-id is required')
    return
  }

  const proverPublicKey = getFlag('--prover')
  if (!proverPublicKey) {
    console.log('--prover public key is required')
    return
  }

  // get all provers
  const proversResponse = await axios.post(
    `https://api.witnesschain.com/proof/v1/${proofType}/provers`,
    {},
    { headers: { Cookie: loginCookies } }
  )

  if (!proversResponse.data?.result?.provers) {
    console.log('No provers found')
    return
  }
  const provers = proversResponse.data.result.provers
  const prover = provers.find(
    (p) => p.id?.toLowerCase().split('/')[1] === proverPublicKey.toLowerCase()
  )
  console.log('PROVER', prover)
  if (!prover) {
    console.log('Prover not found')
    return
  }

  // Trigger challenge
  //   {
  //     "challenge_id": challenge_id,
  //     "prover": prover,
  //     "challenge_type": "downlink"
  // }
  console.log('Trigger challenge...')
  const challengeResponse = await axios.post(
    `https://api.witnesschain.com/proof/v1/${proofType}/challenge-request-dcl`,
    {
      challenge_id: challengeId,
      prover: proverPublicKey,
      challenge_type: 'downlink'
    },
    { headers: { Cookie: loginCookies } }
  )
  console.log('CHALLENGE', challengeResponse.data)

  const statusResponse = await axios.post(
    `https://api.witnesschain.com/proof/v1/${proofType}/challenge-status-dcl`,
    { challenge_id: challengeId },
    {
      headers: {
        Cookie: loginCookies
      }
    }
  )
  console.log('STATUS', statusResponse.data)
}

// Execute the function
triggerChallenge().catch((error) =>
  console.error(error.response?.data || error)
)
