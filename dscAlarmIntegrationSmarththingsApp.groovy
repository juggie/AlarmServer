/**
 *  DSC Alarm Panel integration via REST API callbacks  
 *      
 *  Author: Kent Holloway <drizit@gmail.com>
 */

preferences {
	section("Alarm Panel") {
		input "panel", "device.dSCPanel", title: "Choose Alarm Panel?", multiple: false, required: true
    }
}

mappings {
	path("/panel/:code/:zoneorpart") {
		action: [
			GET: "updateZoneOrPartition"
		]
	}
}

def installed() {
  log.debug "Installed!"
  subscribe(panel)
}

def updated() {
  log.debug "Updated!"
  unsubscribe()
  subscribe(panel)
}

void updateZoneOrPartition() {
	update(panel)
}

private update(panel) {
    // log.debug "update, request: params: ${params} panel: ${panel.name}"

    def zoneorpartition = params.zoneorpart
    def code = params.code
	if (code) 
    {
      // log.debug "Panel:   ${panel.name}"
      // log.debug "Zone/Partition:    ${zoneorpartition}"
      // log.debug "Command: ${code}"
      
      // Codes come in as raw alarm codes from AlarmServer
      // convert them to our device Panel commands
      // OR send in a specific command which will be passed
      // to the device
      def newCommand = ""
      switch(code) {
         case "601": 
           newCommand = "alarm"
           break
         case "602": 
           newCommand = "closed"
           break
         case "609": 
           newCommand = "open"
           break
         case "610":
           newCommand = "closed"
           break
         case "650":
           newCommand = "partitionready"
           break
         case "651":
           newCommand = "partitionnotready"
           break
         case "652":
           newCommand = "partitionarmed"
           break
         case "654":
           newCommand = "partitionalarm"
           break
         case "656":
           newCommand = "partitionexitdelay"
           break
         case "657":
           newCommand = "partitionentrydelay"
           break
         default:
           newCommand = command
           break
      }
      // log.debug "New Command: $newCommand"
      // Send the resulting command
      panel."$newCommand"(zoneorpartition)
    }
}

