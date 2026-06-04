import { useDialog } from 'naive-ui'
import { useI18n } from 'vue-i18n'

export {
  CONFIG_TAB_IDS,
  hotkeyInputValue,
  sliderUnit,
  TAB_IDS,
  useSettingsPanel,
} from '@virtual-tcu/ui/dashboard'
export type { TabId } from '@virtual-tcu/ui/dashboard'

export interface NetworkSavePayload {
  host: string
  webPort: number
  udpPort: number
  udpHubEnabled: boolean
  udpHubTargets: string
}

type NetworkSaveEmit = (
  event: 'saveNetworkAndRestart',
  host: string,
  webPort: number,
  udpPort: number,
  udpHubEnabled: boolean,
  udpHubTargets: string,
) => void

export function useNetworkSaveAction(
  validate: () => NetworkSavePayload | null,
  emit: NetworkSaveEmit,
) {
  function saveNetworkAndRestart() {
    const parsed = validate()
    if (!parsed)
      return
    emit(
      'saveNetworkAndRestart',
      parsed.host,
      parsed.webPort,
      parsed.udpPort,
      parsed.udpHubEnabled,
      parsed.udpHubTargets,
    )
  }

  return { saveNetworkAndRestart }
}

export function useConfirmReset(onConfirm: () => void) {
  const { t } = useI18n()
  const dialog = useDialog()

  function confirmReset() {
    dialog.warning({
      title: t('settings.reset'),
      content: t('settings.resetConfirm'),
      positiveText: t('modal.confirm'),
      negativeText: t('modal.cancel'),
      onPositiveClick: () => {
        onConfirm()
      },
    })
  }

  return { confirmReset }
}
